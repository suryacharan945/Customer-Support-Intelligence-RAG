"""RAG & MCP Pipeline Orchestration Service."""

import time
from typing import Dict, Any, List
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

    def __init__(self):
        self.vector_retriever = VectorStoreRetriever()
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_retriever,
            alpha=settings.HYBRID_SEARCH_ALPHA,
        )
        self.llm_client = LLMClient()

    def _expand_query(self, query: str) -> str:
        """Lightweight query expansion and intent detection."""
        # Detect key domain keywords and augment
        expanded = query
        lower_q = query.lower()
        if "reset" in lower_q or "not working" in lower_q:
            expanded += " factory restore troubleshooting power cycle error"
        return expanded

    async def process_query(self, query: str, session_id: str = "default", top_k: int = 5) -> QueryResponse:
        """Execute end-to-end multi-context RAG flow."""
        start_time = time.time()
        logger.info(f"Processing query: '{query}' for session: '{session_id}'")

        # 1. Query Expansion (Feature 4)
        expanded_query = self._expand_query(query)

        # 2. Hybrid Retrieval (Feature 1 & 2)
        retrieved_contexts = self.hybrid_retriever.retrieve(expanded_query, top_k=top_k)

        # 3. Multi-Context Prompting (MCP) Assembly
        mcp_context_str = MCPContextBuilder.build_context(retrieved_contexts)

        # 4. Prompt Synthesis
        user_prompt = PromptTemplates.MCP_SYNTHESIS_TEMPLATE.format(
            mcp_context=mcp_context_str,
            user_query=query,
        )

        # 5. Remote LLM Generation (Feature 3 & 5)
        llm_output = await self.llm_client.generate_response(
            system_prompt=PromptTemplates.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        answer_text = llm_output.get("text", "")

        # 6. Citations & Confidence Scoring (Feature 7: XAI)
        citations: List[Citation] = []
        scores = []
        for ctx in retrieved_contexts:
            citations.append(
                Citation(
                    document_source=ctx.source,
                    page_or_section=ctx.metadata.get("section", "N/A"),
                    snippet=ctx.text[:150] + "...",
                    relevance_score=round(ctx.score, 4),
                )
            )
            scores.append(ctx.score)

        avg_score = (sum(scores) / len(scores)) if scores else 0.5
        confidence = round(min(1.0, max(0.0, avg_score * 0.95 + 0.05)), 2)

        # 7. Active Learning / Clarification Threshold (Feature 6)
        requires_clarify = confidence < settings.CONFIDENCE_THRESHOLD_CLARIFY
        exec_time = round((time.time() - start_time) * 1000, 2)

        return QueryResponse(
            query=query,
            expanded_query=expanded_query if expanded_query != query else None,
            answer=answer_text,
            confidence_score=confidence,
            citations=citations,
            contexts_used=len(retrieved_contexts),
            execution_time_ms=exec_time,
            requires_human_clarification=requires_clarify,
        )


rag_service = RAGService()
