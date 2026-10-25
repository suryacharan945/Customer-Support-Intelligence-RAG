"""Multi-Context Prompting (MCP) Context Builder.

Fuses heterogeneous contexts (manuals, troubleshooting, FAQs, warranties)
into structured, traceable prompt blocks for LLM reasoning.
"""

from typing import List
from app.retrieval.base import RetrievalResult


class MCPContextBuilder:
    """Constructs structured, multi-source context blocks for prompt augmentation."""

    @staticmethod
    def build_context(retrieval_results: List[RetrievalResult]) -> str:
        """Merge retrieval results into partitioned contextual blocks."""
        if not retrieval_results:
            return "No relevant context found in knowledge base."

        # Group by category / source
        context_blocks = []
        for idx, res in enumerate(retrieval_results, start=1):
            source_tag = res.metadata.get("source", res.source)
            category_tag = res.metadata.get("category", "General").upper()
            relevance_pct = round(res.score * 100, 1)

            block = (
                f"[CONTEXT {idx} | Category: {category_tag} | Source: {source_tag} | Relevance: {relevance_pct}%]\n"
                f"{res.text.strip()}\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)
