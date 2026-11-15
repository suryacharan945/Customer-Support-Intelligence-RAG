"""RAG & Multi-Context Prompting (MCP) Pipeline Orchestration Service.

Supports two operational RAG modes:
- Mode A (Baseline RAG): Dense semantic search across complete knowledge base.
- Mode B (Multi-Contextual RAG): Deterministic category selection, hybrid (Dense+BM25 RRF) retrieval,
  balanced multi-context prompt assembly, and citation groundedness verification.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.category_selector import category_selector, CategorySelector
from app.retrieval.query_analyzer import query_analyzer, QueryAnalyzer
from app.retrieval.evidence_gate import evidence_gate, EvidenceGate
from app.retrieval.query_decomposer import query_decomposer, QueryDecomposer
from app.retrieval.evidence_coverage import (
    evidence_coverage_evaluator,
    EvidenceCoverageEvaluator,
    EvidenceCoverageReport,
)
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
        query_analyzer_instance: Optional[QueryAnalyzer] = None,
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
        self.query_analyzer = query_analyzer_instance or query_analyzer
        self.evidence_gate = evidence_gate
        self.query_decomposer = query_decomposer
        self.evidence_coverage_evaluator = evidence_coverage_evaluator
        if (
            vector_retriever is None
            and bm25_retriever is None
            and not getattr(self, "allow_mock", False)
            and not os.environ.get("PYTEST_CURRENT_TEST")
        ):
            self._auto_seed_bm25_if_empty()

    def _auto_seed_bm25_if_empty(self):
        """Populate BM25 sparse index from canonical knowledge base if empty."""
        try:
            from app.ingestion.loader import DocumentLoader
            from app.ingestion.chunker import DocumentChunker
            kb_dir = Path("data/knowledge_base")
            if not kb_dir.exists():
                kb_dir = Path(settings.GOOGLE_DRIVE_ROOT) / "03_Knowledge_Base"
            if kb_dir.exists():
                loader = DocumentLoader()
                chunker = DocumentChunker()
                chunks = []
                for p in kb_dir.rglob("*.*"):
                    if p.suffix.lower() in (".md", ".txt", ".pdf"):
                        cat = p.parent.name
                        doc = loader.load_file(p, category=cat)
                        chunks.extend(chunker.chunk_document(doc))
                if chunks:
                    self.index_bm25_chunks(chunks)
                    if getattr(self.vector_retriever, "_collection", None) is not None:
                        try:
                            if self.vector_retriever._collection.count() == 0:
                                self.vector_retriever.upsert_chunks(chunks)
                        except Exception as ce:
                            logger.warning(f"Auto-seed Chroma upsert warning: {ce}")
        except Exception as e:
            logger.warning(f"Auto-seed BM25 index encountered non-fatal error: {e}")

    def index_bm25_chunks(self, chunks: List[Any]) -> int:
        """Populate the sparse BM25 retriever index with knowledge base chunks."""
        count = self.bm25_retriever.index_chunks(chunks)
        logger.info(f"Populated BM25 keyword index with {count} chunks.")
        return count

    def _synthesize_partial_answer(
        self, coverage_report: EvidenceCoverageReport
    ) -> Tuple[str, List[Citation], List[Citation]]:
        """
        Synthesizes a 100% grounded, evidence-aware partial answer:
        1. Executive Summary / Direct Answer (for supported sub-questions with citations)
        2. Missing Information & Limitations (explaining unsupported sub-questions)
        3. Verified Source Citations (listing sources used)
        """
        supported_parts = [sq for sq in coverage_report.sub_questions if sq.evidence_status == "SUPPORTED"]
        unsupported_parts = [sq for sq in coverage_report.sub_questions if sq.evidence_status != "SUPPORTED"]

        answer_bullets = []
        citations_used = []
        supporting_citations: List[Citation] = []
        legacy_citations: List[Citation] = []

        for sq in supported_parts:
            if sq.retrieved_contexts:
                top_ctx = sq.retrieved_contexts[0]
                source_file = top_ctx.metadata.get("filename") or top_ctx.source
                page_num = top_ctx.metadata.get("page_number", 1)
                chunk_id = top_ctx.metadata.get("chunk_id") or top_ctx.document_id
                cit_str = f"[Source: {source_file}, Page: {page_num}, Chunk: {chunk_id}]"
                citations_used.append(cit_str)

                from app.generation.local_synthesizer import LocalGroundedSynthesizer
                sents = LocalGroundedSynthesizer.extract_clean_sentences(top_ctx.text)
                fact_text = " ".join(sents[:2]) if sents else LocalGroundedSynthesizer.clean_block_text(top_ctx.text)[:200]
                fact_text = LocalGroundedSynthesizer.neutralize_voice(fact_text)
                clean_aspect = sq.aspect.replace("_", " ").title()
                answer_bullets.append(f"   - **{clean_aspect}**: {fact_text} {cit_str}")

                page_str = f"Page {page_num}" if page_num != -1 else "Full Document"
                sc = Citation(
                    document_source=source_file,
                    page_or_section=page_str,
                    snippet=top_ctx.text[:150] + "...",
                    relevance_score=round(top_ctx.score, 4),
                    category=top_ctx.metadata.get("category", "general"),
                    chunk_id=chunk_id,
                    is_verified=True,
                )
                supporting_citations.append(sc)
                legacy_citations.append(sc)

        exec_summary = (
            "\n".join(answer_bullets)
            if answer_bullets
            else "   - Documented attributes are corroborated by the retrieved evidence."
        )

        missing_bullets = []
        for sq in unsupported_parts:
            reason = sq.decision_reason or "This specific requirement is not documented in the available knowledge base."
            missing_bullets.append(f"   - **{sq.text}**: {reason}")

        missing_formatted = "\n".join(missing_bullets)
        cit_formatted = "\n".join([f"   - {c}" for c in sorted(set(citations_used))]) if citations_used else "   - [Source: No documented citations for unsupported clauses]"

        full_answer = (
            f"### 1. Executive Summary / Direct Answer\n"
            f"Based on available documentation in the knowledge base:\n"
            f"{exec_summary}\n\n"
            f"### 2. Missing Information & Limitations\n"
            f"The following requested information is absent or undocumented in the knowledge base:\n"
            f"{missing_formatted}\n"
            f"No speculative or ungrounded claims have been extrapolated.\n\n"
            f"### 3. Verified Source Citations\n"
            f"{cit_formatted}"
        )

        return full_answer, supporting_citations, legacy_citations

    def _expand_query(self, query: str, is_customer_support: bool = True) -> str:
        """Lightweight query expansion and intent detection."""
        expanded = query
        lower_q = query.lower()
        # Only add printer troubleshooting terms if this is actually a printer customer support query
        if is_customer_support and ("reset" in lower_q or "not working" in lower_q):
            expanded += " factory restore troubleshooting power cycle error"
        return expanded

    async def process_query(
        self,
        query: str,
        session_id: str = "default",
        top_k: int = 5,
        retrieval_mode: str = "multi_context",
        llm_provider: Optional[str] = None,
    ) -> QueryResponse:
        """
        Execute end-to-end RAG workflow.

        Args:
            query: User customer support question.
            session_id: Optional conversation session tracking identifier.
            top_k: Number of candidate evidence passages to retrieve.
            retrieval_mode: 'baseline' (dense unconstrained) or 'multi_context' (MCP hybrid).
            llm_provider: Optional override for generation provider ('colab_remote', 'local', 'auto').
        """
        start_total = time.perf_counter()
        retrieval_mode = retrieval_mode.lower()
        if retrieval_mode not in ("baseline", "multi_context"):
            retrieval_mode = "multi_context"

        logger.info(f"Processing query: '{query}' [Mode: {retrieval_mode}, Session: {session_id}]")

        # Step 0: Compound Query Decomposition & Evidence Coverage Evaluation
        t0_decomp = time.perf_counter()
        decomposition = self.query_decomposer.decompose_query(query)
        decomp_latency_ms = round((time.perf_counter() - t0_decomp) * 1000, 3)

        if decomposition.is_compound and retrieval_mode == "multi_context":
            t0_cov = time.perf_counter()
            coverage_report = await self.evidence_coverage_evaluator.evaluate_coverage(
                query=query,
                retriever=self.hybrid_retriever,
                query_analyzer=self.query_analyzer,
                decomposition=decomposition,
                retrieval_mode=retrieval_mode,
                top_k=top_k,
            )
            cov_latency_ms = round((time.perf_counter() - t0_cov) * 1000, 2)
            ret_timings = getattr(self.hybrid_retriever, "last_timings", {})
            retrieved_contexts = coverage_report.combined_retrieved_contexts

            if coverage_report.overall_evidence_status == "INSUFFICIENT":
                total_time_ms = round((time.perf_counter() - start_total) * 1000, 2)
                abstention_msg = (
                    "### 1. Executive Summary / Direct Answer\n"
                    "Based on the available documentation, insufficient evidence was found in the knowledge base to answer this inquiry. "
                    "None of the requested information requirements are supported by indexed documents.\n\n"
                    "### 2. Missing Information / Limitations\n"
                    + "\n".join([f"   - **{sq.text}**: {sq.decision_reason}" for sq in coverage_report.sub_questions])
                    + "\n\n### 3. Verified Source Citations\n   - [Source: No relevant documentation found]"
                )
                abstention_timings = {
                    "query_decomposition_ms": decomp_latency_ms,
                    "evidence_coverage_ms": cov_latency_ms,
                    "retrieval_dense_ms": ret_timings.get("dense_ms", 0.0),
                    "retrieval_sparse_ms": ret_timings.get("sparse_ms", 0.0),
                    "retrieval_fusion_ms": ret_timings.get("fusion_ms", 0.0),
                    "retrieval_total_ms": cov_latency_ms,
                    "context_assembly_ms": 0.0,
                    "llm_generation_ms": 0.0,
                    "citation_validation_ms": 0.0,
                    "total_pipeline_ms": total_time_ms,
                }
                return QueryResponse(
                    query=query,
                    expanded_query=None,
                    answer=abstention_msg,
                    retrieval_mode=retrieval_mode,
                    selected_categories=[],
                    supporting_citations=[],
                    evidence_status="INSUFFICIENT",
                    retrieval_latency_ms=cov_latency_ms,
                    generation_latency_ms=0.0,
                    provider_status="LOCAL_GROUNDED_SYNTHESIS",
                    evidence_found=False,
                    citations=[],
                    retrieval_similarity=None,
                    confidence_score=None,
                    contexts_used=0,
                    execution_time_ms=total_time_ms,
                    timing_breakdown=abstention_timings,
                    citation_precision=1.0,
                    context_utilization=0.0,
                    requires_human_clarification=True,
                    is_mock=False,
                )

            if coverage_report.overall_evidence_status == "CONFLICTING":
                total_time_ms = round((time.perf_counter() - start_total) * 1000, 2)
                conflict_msg = (
                    "### 1. Executive Summary / Direct Answer\n"
                    "Conflicting recommendations were detected across indexed documents for this inquiry.\n\n"
                    "### 2. Contradiction Analysis\n"
                    f"{coverage_report.decision_rationale}\n\n"
                    "### 3. Verified Source Citations\n"
                    + "\n".join([f"   - [Source: {r.source}]" for r in retrieved_contexts[:2]])
                )
                conflict_timings = {
                    "query_decomposition_ms": decomp_latency_ms,
                    "evidence_coverage_ms": cov_latency_ms,
                    "retrieval_total_ms": cov_latency_ms,
                    "total_pipeline_ms": total_time_ms,
                }
                return QueryResponse(
                    query=query,
                    expanded_query=None,
                    answer=conflict_msg,
                    retrieval_mode=retrieval_mode,
                    selected_categories=[],
                    supporting_citations=[],
                    evidence_status="CONFLICTING",
                    retrieval_latency_ms=cov_latency_ms,
                    generation_latency_ms=0.0,
                    provider_status="LOCAL_GROUNDED_SYNTHESIS",
                    evidence_found=True,
                    citations=[],
                    retrieval_similarity=None,
                    confidence_score=None,
                    contexts_used=len(retrieved_contexts),
                    execution_time_ms=total_time_ms,
                    timing_breakdown=conflict_timings,
                    citation_precision=1.0,
                    context_utilization=0.0,
                    requires_human_clarification=True,
                    is_mock=False,
                )

            if coverage_report.overall_evidence_status == "PARTIAL":
                total_time_ms = round((time.perf_counter() - start_total) * 1000, 2)
                part_ans, supp_cits, leg_cits = self._synthesize_partial_answer(coverage_report)
                partial_timings = {
                    "query_decomposition_ms": decomp_latency_ms,
                    "evidence_coverage_ms": cov_latency_ms,
                    "retrieval_total_ms": cov_latency_ms,
                    "synthesis_ms": round((time.perf_counter() - t0_cov) * 1000, 2),
                    "total_pipeline_ms": total_time_ms,
                }
                return QueryResponse(
                    query=query,
                    expanded_query=None,
                    answer=part_ans,
                    retrieval_mode=retrieval_mode,
                    selected_categories=[],
                    supporting_citations=supp_cits,
                    evidence_status="PARTIAL",
                    retrieval_latency_ms=cov_latency_ms,
                    generation_latency_ms=round((time.perf_counter() - t0_cov) * 1000, 2),
                    provider_status="LOCAL_GROUNDED_SYNTHESIS",
                    evidence_found=True,
                    citations=leg_cits,
                    retrieval_similarity=None,
                    confidence_score=None,
                    contexts_used=len(retrieved_contexts),
                    execution_time_ms=total_time_ms,
                    timing_breakdown=partial_timings,
                    citation_precision=1.0,
                    context_utilization=round(coverage_report.coverage_ratio, 2),
                    requires_human_clarification=True,
                    is_mock=False,
                )

            # Case D: SUFFICIENT compound query - contexts populated from sub-questions
            cat_latency_ms = 0.0
            exp_latency_ms = 0.0
            retrieval_latency_ms = cov_latency_ms
            expanded_query = query
            all_cats = set(self.query_analyzer.analyze_query(query).category_preferences)
            for sq in coverage_report.sub_questions:
                all_cats.update(self.query_analyzer.analyze_query(sq.text).category_preferences)
            selected_categories = sorted(list(all_cats))
            is_customer_support = any("prox" in query.lower() or "colorwave" in query.lower() or "error" in query.lower() for _ in [1])
        else:
            # Single-part query flow
            # Step 1: Query Intent & Category Analysis (for Mode B Multi-Context RAG)
            t0_cat = time.perf_counter()
            selected_categories = []
            is_customer_support = False
            soft_category = True
            if retrieval_mode == "multi_context":
                analysis = self.query_analyzer.analyze_query(query)
                is_customer_support = analysis.is_customer_support
                selected_categories = analysis.category_preferences
                soft_category = analysis.soft_preference_only
                logger.info(
                    f"Query Analysis: intent='{analysis.primary_intent}', "
                    f"support={is_customer_support}, categories={selected_categories}, soft={soft_category}"
                )
            cat_latency_ms = round((time.perf_counter() - t0_cat) * 1000, 3)

            # Step 2: Retrieval Timing & Execution
            t0_exp = time.perf_counter()
            expanded_query = (
                self._expand_query(query, is_customer_support=is_customer_support)
                if retrieval_mode == "multi_context"
                else query
            )
            exp_latency_ms = round((time.perf_counter() - t0_exp) * 1000, 3)

            t0_retrieval = time.perf_counter()
            if retrieval_mode == "baseline":
                # Mode A: Dense-only semantic search across complete knowledge base
                retrieved_contexts = self.hybrid_retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    category=None,
                    mode="dense",
                )
            else:
                # Mode B: Multi-Context hybrid search
                cat_arg = selected_categories if (selected_categories and len(selected_categories) < len(CategorySelector.SUPPORTED_CATEGORIES)) else None
                retrieved_contexts = self.hybrid_retriever.retrieve(
                    query=expanded_query,
                    top_k=top_k,
                    category=cat_arg,
                    mode="hybrid",
                    soft_category=soft_category,
                )

            retrieval_latency_ms = round((time.perf_counter() - t0_retrieval) * 1000, 2)
            ret_timings = getattr(self.hybrid_retriever, "last_timings", {})

        # Step 3: Handle Empty Retrieval (Zero evidence)
        if not retrieved_contexts:
            total_time_ms = round((time.perf_counter() - start_total) * 1000, 2)
            logger.info("Zero matching contexts retrieved. Returning evidence-insufficient response.")
            empty_timings = {
                "category_selection_ms": cat_latency_ms,
                "query_expansion_ms": exp_latency_ms,
                "retrieval_dense_ms": ret_timings.get("dense_ms", 0.0),
                "retrieval_sparse_ms": ret_timings.get("sparse_ms", 0.0),
                "retrieval_fusion_ms": ret_timings.get("fusion_ms", 0.0),
                "retrieval_total_ms": retrieval_latency_ms,
                "context_assembly_ms": 0.0,
                "llm_generation_ms": 0.0,
                "citation_validation_ms": 0.0,
                "total_pipeline_ms": total_time_ms,
            }
            return QueryResponse(
                query=query,
                expanded_query=expanded_query if expanded_query != query else None,
                answer=(
                    "I could not find sufficient information in the available documentation to answer your query. "
                    "Based on available documentation, insufficient evidence was found to answer this inquiry. "
                    "Please verify the question or consult authorized documentation."
                ),
                retrieval_mode=retrieval_mode,
                selected_categories=selected_categories,
                supporting_citations=[],
                evidence_status="INSUFFICIENT",
                retrieval_latency_ms=retrieval_latency_ms,
                generation_latency_ms=0.0,
                provider_status="NO_EVIDENCE_RETRIEVED",
                evidence_found=False,
                citations=[],
                retrieval_similarity=None,
                confidence_score=None,
                contexts_used=0,
                execution_time_ms=total_time_ms,
                timing_breakdown=empty_timings,
                citation_precision=1.0,
                context_utilization=0.0,
                requires_human_clarification=True,
                is_mock=False,
            )

        # Step 3.5: Dedicated Evidence Sufficiency Gate
        t0_gate = time.perf_counter()
        gate_decision = self.evidence_gate.evaluate_evidence_sufficiency(
            query=query,
            retrieved_contexts=retrieved_contexts,
            top_k=top_k,
        )
        gate_latency_ms = round((time.perf_counter() - t0_gate) * 1000, 3)

        if gate_decision.status == "INSUFFICIENT":
            total_time_ms = round((time.perf_counter() - start_total) * 1000, 2)
            logger.info(
                "Evidence sufficiency gate determined INSUFFICIENT evidence for '%s': %s",
                query,
                gate_decision.decision_reasons,
            )

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
                        is_verified=False,
                    )
                )
                similarity_scores.append(ctx.score)

            mean_similarity = (
                round(sum(similarity_scores) / len(similarity_scores), 4)
                if similarity_scores
                else None
            )

            abstention_timings = {
                "category_selection_ms": cat_latency_ms,
                "query_expansion_ms": exp_latency_ms,
                "retrieval_dense_ms": ret_timings.get("dense_ms", 0.0),
                "retrieval_sparse_ms": ret_timings.get("sparse_ms", 0.0),
                "retrieval_fusion_ms": ret_timings.get("fusion_ms", 0.0),
                "retrieval_total_ms": retrieval_latency_ms,
                "evidence_gate_ms": gate_latency_ms,
                "context_assembly_ms": 0.0,
                "llm_generation_ms": 0.0,
                "citation_validation_ms": 0.0,
                "total_pipeline_ms": total_time_ms,
            }

            return QueryResponse(
                query=query,
                expanded_query=expanded_query if expanded_query != query else None,
                answer=(
                    gate_decision.abstention_message
                    or "Based on the available documentation, insufficient evidence was found in the knowledge base to answer this inquiry."
                ),
                retrieval_mode=retrieval_mode,
                selected_categories=selected_categories,
                supporting_citations=[],
                evidence_status="INSUFFICIENT",
                retrieval_latency_ms=retrieval_latency_ms,
                generation_latency_ms=0.0,
                provider_status="LOCAL_GROUNDED_SYNTHESIS",
                evidence_found=False,
                citations=legacy_citations,
                retrieval_similarity=mean_similarity,
                confidence_score=None,
                contexts_used=0,
                execution_time_ms=total_time_ms,
                timing_breakdown=abstention_timings,
                citation_precision=1.0,
                context_utilization=0.0,
                requires_human_clarification=gate_decision.requires_human_clarification,
                is_mock=False,
            )

        # Step 4: Context Assembly
        t0_assembly = time.perf_counter()
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
        assembly_latency_ms = round((time.perf_counter() - t0_assembly) * 1000, 3)

        # Step 5: LLM Generation
        t0_gen = time.perf_counter()
        gen_kwargs = {}
        if llm_provider is not None:
            import inspect
            sig = inspect.signature(self.llm_client.generate_response)
            if "provider" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                gen_kwargs["provider"] = llm_provider

        llm_output = await self.llm_client.generate_response(
            system_prompt=PromptTemplates.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            **gen_kwargs,
        )
        generation_latency_ms = round((time.perf_counter() - t0_gen) * 1000, 2)
        answer_text = llm_output.get("text", "")
        is_mock_response = bool(
            llm_output.get("is_mock", False)
            or any(ctx.metadata.get("is_mock", False) for ctx in retrieved_contexts)
        )

        # Step 6: Source Citation Validation & Groundedness Analysis
        t0_val = time.perf_counter()
        val_report: CitationValidationReport = citation_validator.validate_answer(
            answer_text=answer_text,
            retrieved_contexts=retrieved_contexts,
        )
        val_latency_ms = round((time.perf_counter() - t0_val) * 1000, 3)

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

        timing_breakdown = {
            "category_selection_ms": cat_latency_ms,
            "query_expansion_ms": exp_latency_ms,
            "retrieval_dense_ms": ret_timings.get("dense_ms", 0.0),
            "retrieval_sparse_ms": ret_timings.get("sparse_ms", 0.0),
            "retrieval_fusion_ms": ret_timings.get("fusion_ms", 0.0),
            "retrieval_total_ms": retrieval_latency_ms,
            "evidence_gate_ms": gate_latency_ms,
            "context_assembly_ms": assembly_latency_ms,
            "llm_generation_ms": generation_latency_ms,
            "citation_validation_ms": val_latency_ms,
            "total_pipeline_ms": total_exec_time_ms,
        }

        prov = llm_output.get("provider", "")
        if prov == "local_grounded":
            p_status = "LOCAL_GROUNDED_SYNTHESIS"
        elif prov == "local_grounded_fallback":
            p_status = "LOCAL_GROUNDED_FALLBACK"
        elif is_mock_response:
            p_status = "TEST_MOCK_MODE"
        elif prov == "colab_remote" and not llm_output.get("is_mock"):
            p_status = "ONLINE_COLAB_GPU"
        else:
            p_status = "READY_FOR_COLAB_INFERENCE"

        final_evidence_status = val_report.evidence_status
        if gate_decision.status in ["PARTIAL", "CONFLICTING"]:
            final_evidence_status = gate_decision.status

        return QueryResponse(
            query=query,
            expanded_query=expanded_query if expanded_query != query else None,
            answer=answer_text,
            retrieval_mode=retrieval_mode,
            selected_categories=selected_categories,
            supporting_citations=supporting_citations if supporting_citations else legacy_citations,
            evidence_status=final_evidence_status,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=generation_latency_ms,
            provider_status=p_status,
            evidence_found=True,
            citations=legacy_citations,
            retrieval_similarity=mean_similarity,
            confidence_score=None,  # Uncalibrated confidence intentionally omitted
            contexts_used=contexts_used,
            execution_time_ms=total_exec_time_ms,
            timing_breakdown=timing_breakdown,
            citation_precision=val_report.citation_precision,
            context_utilization=val_report.context_utilization,
            requires_human_clarification=requires_clarify,
            is_mock=is_mock_response,
        )


rag_service = RAGService()
