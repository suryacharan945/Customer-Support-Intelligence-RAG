"""RAG & Multi-Context Prompting (MCP) Pipeline Orchestration Service.

Supports two operational RAG modes:
- Mode A (Baseline RAG): Dense semantic search across complete knowledge base.
- Mode B (Multi-Contextual RAG): Deterministic category selection, hybrid (Dense+BM25 RRF) retrieval,
  balanced multi-context prompt assembly, and citation groundedness verification.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.category_selector import category_selector, CategorySelector
from app.generation.llm_client import LLMClient
from app.generation.mcp_context import MCPContextBuilder, ContextAssemblyResult
from app.generation.prompt_templates import PromptTemplates
from app.generation.citation_validator import citation_validator, CitationValidationReport
from app.api.endpoints.rag import QueryResponse, Citation
from app.core.config import settings
from app.core.logging import logger


class RAGService:
    """
    Orchestrates query classification, hybrid retrieval, multi-context assembly,
    LLM response generation, and source citation validation.
    """

    def __init__(
        self,
        vector_retriever: Optional[VectorStoreRetriever] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        llm_client: Optional[LLMClient] = None,
        allow_mock: Optional[bool] = None,
    ):
        self.allow_mock = allow_mock if allow_mock is not None else settings.ALLOW_MOCK_FALLBACK
        self.vector_retriever = vector_retriever or VectorStoreRetriever(allow_mock=self.allow_mock)
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_retriever,
            bm25_retriever=self.bm25_retriever,
            alpha=settings.HYBRID_SEARCH_ALPHA,
        )
        self.llm_client = llm_client or LLMClient(allow_mock=self.allow_mock)
        self.category_selector = category_selector

    def index_bm25_chunks(self, chunks: List[Any]) -> int:
        """Populate the sparse BM25 retriever index with knowledge base chunks."""
        count = self.bm25_retriever.index_chunks(chunks)
        logger.info(f"Populated BM25 keyword index with {count} chunks.")
        return count

    def _expand_query(self, query: str) -> str:
        """Lightweight query expansion and intent detection."""
        expanded = query
        lower_q = query.lower()
        if "reset" in lower_q or "not working" in lower_q:
            expanded += " factory restore troubleshooting power cycle error"
        return expanded

    async def process_query(
        self,
        query: str,
        session_id: str = "default",
        top_k: int = 5,
        retrieval_mode: str = "multi_context",
    ) -> QueryResponse:
        """
        Execute end-to-end RAG workflow.

        Args:
            query: User customer support question.
            session_id: Optional conversation session tracking identifier.
            top_k: Number of candidate evidence passages to retrieve.
            retrieval_mode: 'baseline' (dense unconstrained) or 'multi_context' (MCP hybrid).
        """
        start_total = time.perf_counter()
        retrieval_mode = retrieval_mode.lower()
        if retrieval_mode not in ("baseline", "multi_context"):
            retrieval_mode = "multi_context"

        logger.info(f"Processing query: '{query}' [Mode: {retrieval_mode}, Session: {session_id}]")

        # Step 1: Query Category Analysis (for Mode B Multi-Context RAG)
        selected_categories: List[str] = []
        if retrieval_mode == "multi_context":
            cat_analysis = self.category_selector.analyze_query(query)
            selected_categories = cat_analysis.selected_categories
            logger.info(f"Selected categories: {selected_categories} (Multi: {cat_analysis.is_multi_category})")

        # Step 2: Retrieval Timing & Execution
        t0_retrieval = time.perf_counter()
        expanded_query = self._expand_query(query) if retrieval_mode == "multi_context" else query

        if retrieval_mode == "baseline":
            # Mode A: Dense-only semantic search across complete knowledge base
            retrieved_contexts = self.hybrid_retriever.retrieve(
                query=query,
                top_k=top_k,
                category=None,
                mode="dense",
            )
        else:
            # Mode B: Multi-Context hybrid search across selected categories
            retrieved_contexts = self.hybrid_retriever.retrieve(
                query=expanded_query,
                top_k=top_k,
                category=selected_categories if len(selected_categories) < len(CategorySelector.SUPPORTED_CATEGORIES) else None,
                mode="hybrid",
            )

        retrieval_latency_ms = round((time.perf_counter() - t0_retrieval) * 1000, 2)

        # Step 3: Handle Empty Retrieval (Zero evidence)
        if not retrieved_contexts:
            total_time_ms = round((time.perf_counter() - start_total) * 1000, 2)
            logger.info("Zero matching contexts retrieved. Returning evidence-insufficient response.")
            return QueryResponse(
                query=query,
                expanded_query=expanded_query if expanded_query != query else None,
                answer=(
                    "I could not find sufficient information in the available documentation to answer your query. "
                    "Based on available ApexPrint documentation, insufficient evidence was found to answer this inquiry. "
                    "Please consult an authorized support technician or submit an inquiry."
                ),
                retrieval_mode=retrieval_mode,
                selected_categories=selected_categories,
                supporting_citations=[],
                evidence_status="INSUFFICIENT",
                retrieval_latency_ms=retrieval_latency_ms,
                generation_latency_ms=0.0,
                evidence_found=False,
                citations=[],
                retrieval_similarity=None,
                confidence_score=None,
                contexts_used=0,
                execution_time_ms=total_time_ms,
                requires_human_clarification=True,
                is_mock=False,
            )

        # Step 4: Context Assembly
        if retrieval_mode == "baseline":
            # Simple context concatenation for baseline mode
            blocks = []
            for idx, r in enumerate(retrieved_contexts, start=1):
                blocks.append(f"[Excerpt {idx} - Source: {r.source}]\n{r.text}\n")
            context_str = "\n".join(blocks)
            user_prompt = PromptTemplates.BASELINE_SYNTHESIS_TEMPLATE.format(
                context_blocks=context_str,
                user_query=query,
            )
            contexts_used = len(retrieved_contexts)
        else:
            # Multi-Context Prompting (MCP) Assembly
            mcp_result: ContextAssemblyResult = MCPContextBuilder.build_context(
                retrieved_contexts,
                max_chars=8000,
                balance_categories=True,
            )
            conflict_notice = mcp_result.conflict_notes or "No inter-category documentation conflict detected."
            user_prompt = PromptTemplates.MCP_SYNTHESIS_TEMPLATE.format(
                mcp_context=mcp_result.formatted_context,
                conflict_notice=conflict_notice,
                user_query=query,
            )
            contexts_used = mcp_result.total_chunks_used

        # Step 5: LLM Generation
        t0_gen = time.perf_counter()
        llm_output = await self.llm_client.generate_response(
            system_prompt=PromptTemplates.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        generation_latency_ms = round((time.perf_counter() - t0_gen) * 1000, 2)
        answer_text = llm_output.get("text", "")
        is_mock_response = bool(
            llm_output.get("is_mock", False)
            or any(ctx.metadata.get("is_mock", False) for ctx in retrieved_contexts)
        )

        # Step 6: Source Citation Validation & Groundedness Analysis
        val_report: CitationValidationReport = citation_validator.validate_answer(
            answer_text=answer_text,
            retrieved_contexts=retrieved_contexts,
        )

        # Convert verified citations to Citation schema
        supporting_citations: List[Citation] = []
        for vc in val_report.verified_citations:
            page_str = f"Page {vc.page_number}" if vc.page_number is not None and vc.page_number != -1 else "Full Document"
            supporting_citations.append(
                Citation(
                    document_source=vc.source_file,
                    page_or_section=page_str,
                    snippet=vc.snippet,
                    relevance_score=vc.relevance_score,
                    category=vc.category,
                    chunk_id=vc.chunk_id,
                    is_verified=vc.is_verified,
                )
            )

        # Backward-compatible citations list
        legacy_citations: List[Citation] = []
        similarity_scores: List[float] = []
        for ctx in retrieved_contexts:
            page_num = ctx.metadata.get("page_number")
            page_str = f"Page {page_num}" if page_num is not None and page_num != -1 else ctx.metadata.get("section", "N/A")
            legacy_citations.append(
                Citation(
                    document_source=ctx.metadata.get("filename") or ctx.source,
                    page_or_section=page_str,
                    snippet=ctx.text[:150] + "...",
                    relevance_score=round(ctx.score, 4),
                    category=ctx.metadata.get("category", "general"),
                    chunk_id=ctx.metadata.get("chunk_id") or ctx.document_id,
                    is_verified=True,
                )
            )
            similarity_scores.append(ctx.score)

        mean_similarity = (
            round(sum(similarity_scores) / len(similarity_scores), 4)
            if similarity_scores
            else None
        )

        requires_clarify = (
            mean_similarity is not None
            and mean_similarity < settings.CONFIDENCE_THRESHOLD_CLARIFY
        )
        total_exec_time_ms = round((time.perf_counter() - start_total) * 1000, 2)

        return QueryResponse(
            query=query,
            expanded_query=expanded_query if expanded_query != query else None,
            answer=answer_text,
            retrieval_mode=retrieval_mode,
            selected_categories=selected_categories,
            supporting_citations=supporting_citations if supporting_citations else legacy_citations,
            evidence_status=val_report.evidence_status,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=generation_latency_ms,
            evidence_found=True,
            citations=legacy_citations,
            retrieval_similarity=mean_similarity,
            confidence_score=None,  # Uncalibrated confidence intentionally omitted
            contexts_used=contexts_used,
            execution_time_ms=total_exec_time_ms,
            requires_human_clarification=requires_clarify,
            is_mock=is_mock_response,
        )


rag_service = RAGService()
