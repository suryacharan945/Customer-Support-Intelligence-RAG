"""Source Citations and Groundedness Display Component.

Renders verified supporting citations and retrieved candidate chunks.
Enforces:
- Exact metadata display (no invented fields)
- Clear distinction between verified support and candidate evidence
- Grounded excerpt display with relevance scores
"""

from typing import List, Dict, Any, Optional
import streamlit as st
from frontend.components.badges import get_category_badge_html


def render_citations(
    supporting_citations: List[Dict[str, Any]],
    candidate_citations: Optional[List[Dict[str, Any]]] = None,
    expanded: bool = False,
) -> None:
    """
    Render supporting citations and candidate retrieval evidence.
    
    Args:
        supporting_citations: Verified citations directly backing the generated response.
        candidate_citations: Optional retrieved candidate chunks from knowledge base.
        expanded: Whether the citation section should start expanded.
    """
    total_supporting = len(supporting_citations)
    total_candidates = len(candidate_citations or [])

    with st.expander(
        f"📚 Sources & Citations ({total_supporting} verified support, {total_candidates} candidates)",
        expanded=expanded,
    ):
        if not supporting_citations and not candidate_citations:
            st.info("No supporting evidence or candidate citations returned for this query.")
            return

        if supporting_citations:
            st.markdown("#### ✅ Verified Supporting Citations")
            st.caption("Passages directly referenced and verified as ground truth for the synthesis.")

            for i, cite in enumerate(supporting_citations, start=1):
                doc_source = cite.get("document_source", "Unknown Document")
                category = cite.get("category", "general")
                page_info = cite.get("page_or_section")
                snippet = cite.get("snippet", "")
                relevance = cite.get("relevance_score")
                chunk_id = cite.get("chunk_id")
                is_verified = cite.get("is_verified", True)

                cat_badge = get_category_badge_html(category)
                page_str = f" • **{page_info}**" if page_info else ""
                rel_str = f" • Score: `{round(relevance * 100, 1)}%`" if relevance is not None else ""
                chunk_str = f" • ID: `{chunk_id}`" if chunk_id else ""
                verified_str = " • <span style='color:#15803d; font-weight:600;'>[Verified]</span>" if is_verified else ""

                st.markdown(
                    f"""
                    <div style="border-left: 3px solid #16a34a; background-color: #f9fafb; padding: 10px 14px; margin-bottom: 10px; border-radius: 4px;">
                        <div style="margin-bottom: 6px;">
                            <strong>[{i}] {doc_source}</strong>{page_str}{chunk_str}{rel_str} {cat_badge}{verified_str}
                        </div>
                        <div style="font-size: 13px; color: #374151; font-style: italic; background-color: #ffffff; padding: 8px 12px; border-radius: 4px; border: 1px solid #e5e7eb;">
                            "{snippet}"
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if candidate_citations:
            st.markdown("#### 🔍 Retrieved Candidate Evidence")
            st.caption("Additional relevant passages retrieved from knowledge base during hybrid search.")

            for i, cand in enumerate(candidate_citations, start=1):
                # Avoid re-displaying identical chunks already displayed in supporting
                cand_chunk_id = cand.get("chunk_id")
                if supporting_citations and any(s.get("chunk_id") == cand_chunk_id for s in supporting_citations if cand_chunk_id):
                    continue

                doc_source = cand.get("document_source", "Unknown Document")
                category = cand.get("category", "general")
                page_info = cand.get("page_or_section")
                snippet = cand.get("snippet", "")
                relevance = cand.get("relevance_score")
                chunk_id = cand.get("chunk_id")

                cat_badge = get_category_badge_html(category)
                page_str = f" • **{page_info}**" if page_info else ""
                rel_str = f" • Score: `{round(relevance * 100, 1)}%`" if relevance is not None else ""
                chunk_str = f" • ID: `{chunk_id}`" if chunk_id else ""

                st.markdown(
                    f"""
                    <div style="border-left: 3px solid #6b7280; background-color: #f9fafb; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px;">
                        <div style="margin-bottom: 4px; font-size: 13px;">
                            <strong>{doc_source}</strong>{page_str}{chunk_str}{rel_str} {cat_badge}
                        </div>
                        <div style="font-size: 12px; color: #4b5563; background-color: #ffffff; padding: 6px 10px; border-radius: 4px; border: 1px solid #e5e7eb;">
                            "{snippet}"
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
