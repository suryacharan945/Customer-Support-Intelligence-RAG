"""RAG & MCP Pipeline Orchestration Service with conservative evidence citations and uncalibrated metric isolation."""

import time
from typing import Dict, Any, List, Optional
from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.hybrid import HybridRetriever
from app.generation.llm_client import LLMClient
from app.generation.mcp_context import MCPContextBuilder
from app.generation.prompt_templates import PromptTemplates
from app.api.endpoints.rag import QueryResponse, Citation
from app.core.config import settings
from app.core.logging import logger


class RAGService:
    """Orchestrates query expansion, hybrid retrieval, MCP fusion, and LLM synthesis."""

    def __init__(
        self,
        vector_retriever: Optional[VectorStoreRetriever] = None,
        llm_client: Optional[LLMClient] = None,
        allow_mock: Optional[bool] = None,
    ):
        self.allow_mock = allow_mock if allow_mock is not None else settings.ALLOW_MOCK_FALLBACK
        self.vector_retriever = vector_retriever or VectorStoreRetriever(allow_mock=self.allow_mock)
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_retriever,
            alpha=settings.HYBRID_SEARCH_ALPHA,
        )
        self.llm_client = llm_client or LLMClient(allow_mock=self.allow_mock)

    def _expand_query(self, query: str) -> str:
        """Lightweight query expansion and intent detection."""
        expanded = query
        lower_q = query.lower()
        if "reset" in lower_q or "not working" in lower_q:
            expanded += " factory restore troubleshooting power cycle error"
        return expanded

    async def process_query(self, query: str, session_id: str = "default", top_k: int = 5) -> QueryResponse:
        """
        Execute end-to-end multi-context RAG flow.
        Adheres to conservative evidence policy:
        - When no contexts match, returns an evidence-insufficient response without LLM hallucination.
        - Emits uncalibrated retrieval similarity without fabricating an artificial correctness probability.
        - Flags mock outputs explicitly.
        """
        start_time = time.time()
        logger.info(f"Processing query: '{query}' for session: '{session_id}'")

        # 1. Query Expansion (Feature 4)
        expanded_query = self._expand_query(query)

        # 2. Hybrid Retrieval (Feature 1 & 2)
        retrieved_contexts = self.hybrid_retriever.retrieve(expanded_query, top_k=top_k)

        # 3. Handle Empty Retrieval (Zero evidence)
        if not retrieved_contexts:
            exec_time = round((time.time() - start_time) * 1000, 2)
            logger.info("Zero matching contexts retrieved. Returning evidence-insufficient response.")
            return QueryResponse(
                query=query,
                expanded_query=expanded_query if expanded_query != query else None,
                answer=(
                    "I could not find sufficient information in the available documentation to answer your query. "
                    "Please consult an authorized support technician or submit an inquiry."
                ),
                evidence_found=False,
                citations=[],
                retrieval_similarity=None,
                confidence_score=None,
                contexts_used=0,
                execution_time_ms=exec_time,
                requires_human_clarification=True,
                is_mock=False,
            )

        # 4. Multi-Context Prompting (MCP) Assembly
        mcp_context_str = MCPContextBuilder.build_context(retrieved_contexts)

        # 5. Prompt Synthesis
        user_prompt = PromptTemplates.MCP_SYNTHESIS_TEMPLATE.format(
            mcp_context=mcp_context_str,
            user_query=query,
        )

        # 6. Remote LLM Generation (Feature 3 & 5)
        llm_output = await self.llm_client.generate_response(
            system_prompt=PromptTemplates.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        answer_text = llm_output.get("text", "")
        is_mock_response = bool(
            llm_output.get("is_mock", False)
            or any(ctx.metadata.get("is_mock", False) for ctx in retrieved_contexts)
        )

        # 7. Conservative Evidence-Backed Citations (Feature 7: XAI)
        citations: List[Citation] = []
        similarity_scores: List[float] = []
        for ctx in retrieved_contexts:
            citations.append(
                Citation(
                    document_source=ctx.source,
                    page_or_section=ctx.metadata.get("section", "N/A"),
                    snippet=ctx.text[:150] + "...",
                    relevance_score=round(ctx.score, 4),
                )
            )
            similarity_scores.append(ctx.score)

        # Compute uncalibrated retrieval similarity (mean of retrieved contexts)
        mean_similarity = (
            round(sum(similarity_scores) / len(similarity_scores), 4)
            if similarity_scores
            else None
        )

        # Active Learning / Clarification Threshold: Flag if similarity is below threshold
        requires_clarify = (
            mean_similarity is not None
            and mean_similarity < settings.CONFIDENCE_THRESHOLD_CLARIFY
        )
        exec_time = round((time.time() - start_time) * 1000, 2)

        return QueryResponse(
            query=query,
            expanded_query=expanded_query if expanded_query != query else None,
            answer=answer_text,
            evidence_found=True,
            citations=citations,
            retrieval_similarity=mean_similarity,
            confidence_score=None,  # Uncalibrated confidence intentionally omitted until calibrated module is built
            contexts_used=len(retrieved_contexts),
            execution_time_ms=exec_time,
            requires_human_clarification=requires_clarify,
            is_mock=is_mock_response,
        )


rag_service = RAGService()
