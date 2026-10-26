"""Page C: Baseline vs Multi-Context RAG Comparison View.

Enables side-by-side evaluation of single-channel Baseline RAG versus
Multi-Context Prompting (MCP) Hybrid RAG for the identical user question.
Strictly adheres to:
- Real-time side-by-side execution
- Transparent reporting of provider inference availability
- Zero fabrication of historical scores as live metrics
"""

from typing import Dict, Any, Optional
import streamlit as st

from frontend.api_client import APIClient, APIClientError, APIConnectionError
from frontend.components.badges import (
    get_provider_badge_html,
    get_evidence_badge_html,
    get_category_badge_html,
)
from frontend.components.citations import render_citations

SAMPLE_COMPARISON_QUERIES = [
    "What is the warranty coverage for ProX-400 and how to fix error E-101?",
    "Can I return an opened printer if the printhead is defective?",
    "How do I clear error code E-204 and is it covered under standard warranty?",
    "What maintenance procedures are required for ColorWave 850 monthly?",
]


def render_comparison_view(api_client: APIClient) -> None:
    """Render side-by-side RAG mode comparison interface."""
    st.markdown("## ⚖️ Baseline vs Multi-Context RAG Comparison")
    st.markdown(
        "Execute a single query across both **Mode A (Baseline Single-Channel Dense)** and "
        "**Mode B (Multi-Context Hybrid MCP)** under identical retrieval settings to evaluate "
        "retrieval precision, category routing, and evidence groundedness."
    )

    # Input Section
    col_q, col_k = st.columns([4, 1])

    with col_q:
        comp_query = st.text_input(
            "Enter customer support inquiry to compare",
            placeholder="e.g. What is the warranty coverage for ProX-400 and how to fix error E-101?",
            key="input_comp_query",
        )

    with col_k:
        comp_top_k = st.slider("Top-K Candidates", min_value=1, max_value=10, value=5, step=1, key="comp_top_k")

    # Sample Buttons
    st.caption("💡 Quick Comparison Inquiries:")
    c_cols = st.columns(len(SAMPLE_COMPARISON_QUERIES))
    for i, sample in enumerate(SAMPLE_COMPARISON_QUERIES):
        if c_cols[i].button(f"Option {i+1}", help=sample, key=f"btn_comp_sample_{i}"):
            comp_query = sample

    run_comp = st.button("🚀 Run Comparative Analysis", type="primary", key="btn_run_comp")

    if run_comp:
        if not comp_query or not comp_query.strip():
            st.warning("Please enter a customer inquiry to execute the comparison.")
            return

        with st.spinner("Executing dual-channel retrieval and evaluation against knowledge base..."):
            try:
                # 1. Run Baseline Mode
                baseline_res = api_client.query(
                    query=comp_query.strip(),
                    retrieval_mode="baseline",
                    top_k=comp_top_k,
                    session_id="comparison-baseline",
                )

                # 2. Run Multi-Context Mode
                multi_res = api_client.query(
                    query=comp_query.strip(),
                    retrieval_mode="multi_context",
                    top_k=comp_top_k,
                    session_id="comparison-multicontext",
                )

                st.session_state.comparison_data = {
                    "query": comp_query.strip(),
                    "baseline": baseline_res,
                    "multi_context": multi_res,
                }

            except APIConnectionError:
                st.error(f"🔌 Backend Offline: Unable to reach FastAPI service at `{api_client.base_url}`.")
                return
            except APIClientError as e:
                st.error(f"❌ API Error during comparison: {str(e)}")
                return

    # Display comparison results if present in session state
    if st.session_state.comparison_data:
        comp_data = st.session_state.comparison_data
        b_res = comp_data["baseline"]
        m_res = comp_data["multi_context"]
        query_text = comp_data["query"]

        st.markdown(f"### 📋 Comparison Results for: *\"{query_text}\"*")

        col_left, col_right = st.columns(2)

        # ----------------------------------------------------------------------
        # Column 1: Mode A (Baseline RAG)
        # ----------------------------------------------------------------------
        with col_left:
            st.markdown(
                """
                <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                    <h4 style="margin:0 0 6px 0; color: #334155;">Mode A: Baseline RAG</h4>
                    <span style="font-size: 12px; color: #64748b;">Single-Channel Dense Semantic Retrieval (Unconstrained)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Metadata metrics
            b_ret_lat = b_res.get("retrieval_latency_ms", 0.0)
            b_ev_status = b_res.get("evidence_status", "SUFFICIENT")
            b_prov_st = b_res.get("provider_status", "UNKNOWN")
            b_supp_cites = b_res.get("supporting_citations", [])
            b_cats = b_res.get("selected_categories", [])

            st.markdown(
                f"<div style='margin-bottom:10px; font-size:12px;'>"
                f"{get_provider_badge_html(b_prov_st)} • {get_evidence_badge_html(b_ev_status)}<br/>"
                f"⚡ Retrieval Latency: <strong>{b_ret_lat} ms</strong><br/>"
                f"📂 Category Focus: <em>{'All Knowledge Base' if not b_cats else ', '.join(b_cats)}</em>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if "READY_FOR_COLAB" in b_prov_st.upper():
                st.info("ℹ️ Remote GPU generation in standby. Retrieved evidence shown below.")

            st.markdown("##### Synthesized Answer:")
            st.markdown(b_res.get("answer", ""))

            render_citations(
                supporting_citations=b_supp_cites,
                candidate_citations=b_res.get("citations", []),
                expanded=True,
            )

        # ----------------------------------------------------------------------
        # Column 2: Mode B (Multi-Context RAG)
        # ----------------------------------------------------------------------
        with col_right:
            st.markdown(
                """
                <div style="background-color: #eff6ff; border: 1px solid #93c5fd; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                    <h4 style="margin:0 0 6px 0; color: #1e3a8a;">Mode B: Multi-Context RAG (MCP)</h4>
                    <span style="font-size: 12px; color: #1d4ed8;">Category Intent Routing + Hybrid Search (Dense+BM25)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Metadata metrics
            m_ret_lat = m_res.get("retrieval_latency_ms", 0.0)
            m_ev_status = m_res.get("evidence_status", "SUFFICIENT")
            m_prov_st = m_res.get("provider_status", "UNKNOWN")
            m_supp_cites = m_res.get("supporting_citations", [])
            m_cats = m_res.get("selected_categories", [])

            cat_badges = " ".join(get_category_badge_html(c) for c in m_cats) if m_cats else "*(All)*"

            st.markdown(
                f"<div style='margin-bottom:10px; font-size:12px;'>"
                f"{get_provider_badge_html(m_prov_st)} • {get_evidence_badge_html(m_ev_status)}<br/>"
                f"⚡ Retrieval Latency: <strong>{m_ret_lat} ms</strong><br/>"
                f"📂 Detected Categories: {cat_badges}"
                f"</div>",
                unsafe_allow_html=True,
            )

            if "READY_FOR_COLAB" in m_prov_st.upper():
                st.info("ℹ️ Remote GPU generation in standby. Retrieved evidence shown below.")

            st.markdown("##### Synthesized Answer:")
            st.markdown(m_res.get("answer", ""))

            render_citations(
                supporting_citations=m_supp_cites,
                candidate_citations=m_res.get("citations", []),
                expanded=True,
            )

        # ----------------------------------------------------------------------
        # Side-by-Side Diagnostic Summary
        # ----------------------------------------------------------------------
        st.divider()
        st.markdown("#### 📊 Comparative Retrieval Metrics")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            label="Baseline Latency",
            value=f"{b_ret_lat:.1f} ms",
        )
        m2.metric(
            label="Multi-Context Latency",
            value=f"{m_ret_lat:.1f} ms",
            delta=f"{m_ret_lat - b_ret_lat:+.1f} ms",
            delta_color="inverse",
        )
        m3.metric(
            label="Baseline Verified Citations",
            value=len(b_supp_cites),
        )
        m4.metric(
            label="Multi-Context Verified Citations",
            value=len(m_supp_cites),
            delta=f"{len(m_supp_cites) - len(b_supp_cites):+d}",
        )
