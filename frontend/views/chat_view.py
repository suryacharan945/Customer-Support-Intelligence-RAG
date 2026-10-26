"""Page A: Customer Support Chat Assistant View.

Enables interactive questioning against the ApexPrint enterprise knowledge base.
Provides:
- Mode toggle: Baseline (Dense) vs Multi-Context (MCP Hybrid)
- Optional category focus
- Top-K retrieval depth control
- Latency, groundedness, and provider status telemetry
- Interactive citation inspection and feedback loop
"""

from typing import Optional, Dict, Any
import streamlit as st

from frontend.api_client import APIClient, APIClientError, APIConnectionError
from frontend.state import add_chat_turn, clear_chat_history
from frontend.components.badges import (
    get_provider_badge_html,
    get_evidence_badge_html,
    get_category_badge_html,
)
from frontend.components.citations import render_citations
from frontend.components.feedback_widget import render_feedback_widget


EXAMPLE_QUERIES = [
    "What is the warranty coverage for ProX-400 and how to fix error E-101?",
    "How do I clear a paper jam in feed tray B on the ApexPrint ColorWave 850?",
    "Is print head damage covered under standard warranty or SLA tier 2?",
    "What should I do when error code E-204 appears on the control panel?",
]


def render_chat_view(api_client: APIClient) -> None:
    """Render the primary customer support chat interface."""
    st.markdown("## 💬 Customer Support Intelligence Assistant")
    st.markdown(
        "Ask technical, warranty, or troubleshooting questions grounded directly in the "
        "ApexPrint enterprise knowledge base. Switch between **Baseline** and **Multi-Context** RAG."
    )

    # Top Control Bar
    with st.expander("⚙️ Retrieval & Prompting Configuration", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            mode_choice = st.radio(
                "RAG Retrieval Strategy",
                options=["Multi-Context (MCP Hybrid)", "Baseline (Dense Only)"],
                index=0 if st.session_state.retrieval_mode == "multi_context" else 1,
                help=(
                    "Multi-Context analyzes query intent across categories, performs hybrid (Dense+BM25) search, "
                    "and merges balanced contexts. Baseline performs single-channel dense retrieval across all documents."
                ),
                key="rag_mode_radio",
            )
            st.session_state.retrieval_mode = (
                "multi_context" if "Multi-Context" in mode_choice else "baseline"
            )

        with col2:
            cat_choice = st.selectbox(
                "Category Focus (Optional Filter)",
                options=[
                    "All Categories (Auto-Detect)",
                    "troubleshooting",
                    "warranty",
                    "product_manual",
                    "faq",
                ],
                index=0,
                key="category_focus_select",
            )

        with col3:
            top_k = st.slider(
                "Top-K Chunks",
                min_value=1,
                max_value=10,
                value=st.session_state.top_k,
                step=1,
                help="Maximum candidate evidence chunks to retrieve from knowledge base.",
                key="top_k_slider",
            )
            st.session_state.top_k = top_k

    # Quick Example Buttons
    st.caption("💡 Quick Example Inquiries:")
    cols = st.columns(len(EXAMPLE_QUERIES))
    selected_example: Optional[str] = None
    for i, ex in enumerate(EXAMPLE_QUERIES):
        if cols[i].button(f"📌 Q{i+1}", help=ex, key=f"ex_btn_{i}"):
            selected_example = ex

    # Chat History Display
    if st.session_state.chat_history:
        col_title, col_clear = st.columns([5, 1])
        with col_clear:
            if st.button("🗑️ Clear Chat", key="btn_clear_chat"):
                clear_chat_history()
                st.rerun()

        for idx, turn in enumerate(st.session_state.chat_history):
            turn_id = turn.get("turn_id", f"turn_{idx}")
            user_q = turn.get("query", "")
            assistant_ans = turn.get("answer", "")
            mode = turn.get("retrieval_mode", "multi_context")
            cats = turn.get("selected_categories", [])
            provider_st = turn.get("provider_status", "UNKNOWN")
            evidence_st = turn.get("evidence_status", "SUFFICIENT")
            ret_latency = turn.get("retrieval_latency_ms", 0.0)
            gen_latency = turn.get("generation_latency_ms")
            supp_citations = turn.get("supporting_citations", [])
            cand_citations = turn.get("candidate_citations", [])

            # User Bubble
            with st.chat_message("user"):
                st.markdown(f"**{user_q}**")

            # Assistant Bubble
            with st.chat_message("assistant"):
                # Metadata line
                mode_label = "🔷 Multi-Context RAG" if mode == "multi_context" else "⚪ Baseline RAG"
                cat_badges = " ".join(get_category_badge_html(c) for c in cats) if cats else "*(Single-Channel)*"
                provider_badge = get_provider_badge_html(provider_st)
                evidence_badge = get_evidence_badge_html(evidence_st)
                latency_str = f"⚡ Latency: `{ret_latency}ms` (retrieval)"
                if gen_latency:
                    latency_str += f" + `{gen_latency}ms` (generation)"

                st.markdown(
                    f"<div style='font-size:12px; margin-bottom:8px;'>"
                    f"<strong>{mode_label}</strong> • {provider_badge} • {evidence_badge} • {latency_str}"
                    f"<div style='margin-top:4px;'>Selected Categories: {cat_badges}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Provider notice if on standby
                if "READY_FOR_COLAB" in provider_st.upper():
                    st.info(
                        "ℹ️ **Inference Runtime Note**: The remote Colab GPU inference node is currently in standby. "
                        "Grounded knowledge-base evidence was successfully retrieved below. "
                        "When active, full text synthesis is generated via Mistral-7B."
                    )

                # Answer Text
                st.markdown(assistant_ans)

                # Citations
                render_citations(
                    supporting_citations=supp_citations,
                    candidate_citations=cand_citations,
                    expanded=(idx == len(st.session_state.chat_history) - 1),
                )

                # Feedback widget
                render_feedback_widget(api_client=api_client, turn_id=turn_id, query=user_q)
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #d1d5db; border-radius: 8px; padding: 30px; text-align: center; color: #6b7280; margin: 20px 0;">
                <p style="font-size: 16px; font-weight: 500; margin-bottom: 6px;">No conversations yet</p>
                <p style="font-size: 13px;">Type a customer support inquiry below or click one of the quick example prompts above.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Chat Input Box
    prompt_input = st.chat_input("Enter customer support question here...")
    active_query = selected_example or prompt_input

    if active_query:
        # Check query validity
        if not active_query.strip():
            st.warning("Please enter a valid, non-empty query.")
            return

        with st.spinner("🔍 Querying ApexPrint knowledge base and verifying citations..."):
            try:
                retrieval_mode = st.session_state.retrieval_mode
                top_k_val = st.session_state.top_k

                # Optional manual category focus hint
                final_query = active_query
                if cat_choice and cat_choice != "All Categories (Auto-Detect)":
                    final_query = f"[{cat_choice}] {active_query}"

                response = api_client.query(
                    query=final_query,
                    retrieval_mode=retrieval_mode,
                    top_k=top_k_val,
                    session_id=st.session_state.session_id,
                )

                add_chat_turn(query=active_query, response=response)
                st.rerun()

            except APIConnectionError as e:
                st.error(
                    f"🔌 **Backend Offline**: Unable to connect to FastAPI backend at `{api_client.base_url}`.\n\n"
                    "Please ensure the backend is running with:\n"
                    "```bash\n"
                    "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000\n"
                    "```"
                )
            except APIClientError as e:
                st.error(f"❌ **API Error**: {str(e)}")
            except Exception as e:
                st.error(f"⚠️ **Unexpected Error**: {str(e)}")
