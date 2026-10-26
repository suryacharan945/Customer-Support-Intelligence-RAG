"""Page D: Knowledge Base & Telemetry Analytics View.

Displays live status of the knowledge base, 6-state lifecycle distribution,
category coverage, ChromaDB vector collection metrics, and subsystem readiness.
Strictly renders genuine backend telemetry.
"""

from typing import Dict, Any, List
import streamlit as st

from frontend.api_client import APIClient, APIClientError, APIConnectionError


def render_knowledge_base_view(api_client: APIClient) -> None:
    """Render knowledge base status and subsystem telemetry."""
    st.markdown("## 📊 Knowledge Base Status & Subsystem Diagnostics")
    st.markdown(
        "Real-time operational telemetry queried directly from the FastAPI backend and persistent ingestion manifest."
    )

    col_ref, _ = st.columns([1, 5])
    with col_ref:
        if st.button("🔄 Refresh Telemetry", key="btn_refresh_kb"):
            st.rerun()

    try:
        # Fetch status and readiness
        kb_status = api_client.get_knowledge_base_status()
        ready_status = api_client.get_ready()

        # ----------------------------------------------------------------------
        # Section 1: Overview Metrics
        # ----------------------------------------------------------------------
        total_docs = kb_status.get("total_active_documents", 0)
        searchable_docs = kb_status.get("searchable_documents_count", 0)
        total_chunks = kb_status.get("total_active_chunks", 0)
        vector_chunks = kb_status.get("vector_store", {}).get("total_indexed_chunks", 0)

        st.markdown("### 📈 Core Corpus Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Active Documents", total_docs)
        m2.metric("Searchable in RAG", searchable_docs)
        m3.metric("Semantic Chunks", total_chunks)
        m4.metric("ChromaDB Vectors", vector_chunks)

        # ----------------------------------------------------------------------
        # Section 2: Lifecycle Breakdown (6 States)
        # ----------------------------------------------------------------------
        st.markdown("### 🔄 Ingestion Lifecycle State Machine (6 States)")
        lifecycle_counts: Dict[str, int] = kb_status.get("documents_by_lifecycle_status", {})

        lc_cols = st.columns(6)
        states_def = [
            ("uploaded", "📥 Uploaded", "#6b7280"),
            ("processed", "⚙️ Processed", "#3b82f6"),
            ("pending_index", "⏳ Pending Index", "#eab308"),
            ("indexed", "✅ Indexed", "#22c55e"),
            ("indexing_failed", "❌ Failed", "#ef4444"),
            ("deleted", "🗑️ Deleted", "#9ca3af"),
        ]

        for i, (state_key, label, color) in enumerate(states_def):
            count = lifecycle_counts.get(state_key, 0)
            lc_cols[i].markdown(
                f"""
                <div style="background-color: #f9fafb; border-top: 3px solid {color}; border-radius: 6px; padding: 10px; text-align: center; border: 1px solid #e5e7eb;">
                    <div style="font-size: 11px; font-weight: 600; color: #4b5563;">{label}</div>
                    <div style="font-size: 20px; font-weight: 700; color: #111827; margin-top: 4px;">{count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------------------------
        # Section 3: Category Coverage
        # ----------------------------------------------------------------------
        st.markdown("### 📂 Document Distribution by Category")
        category_counts: Dict[str, int] = kb_status.get("documents_by_category", {})

        cat_col_left, cat_col_right = st.columns([1, 1])

        with cat_col_left:
            st.markdown("#### Category Breakdown")
            for cat_name, cnt in category_counts.items():
                pct = (cnt / total_docs * 100) if total_docs > 0 else 0
                st.markdown(f"- **{cat_name.replace('_', ' ').title()}**: `{cnt}` documents (`{pct:.1f}%`)")

        with cat_col_right:
            st.markdown("#### Corpus Balance Visualizer")
            for cat_name, cnt in category_counts.items():
                ratio = min(max(cnt / total_docs, 0.0), 1.0) if total_docs > 0 else 0.0
                st.progress(ratio, text=f"{cat_name.replace('_', ' ').title()} ({ratio*100:.1f}%)")

        # ----------------------------------------------------------------------
        # Section 4: Subsystem Readiness & Storage Telemetry
        # ----------------------------------------------------------------------
        st.markdown("### 🖥️ Subsystem Readiness & Storage Telemetry")
        checks = ready_status.get("checks", {})
        storage_meta = kb_status.get("storage", {})
        vector_meta = kb_status.get("vector_store", {})

        s1, s2 = st.columns(2)

        with s1:
            st.markdown("#### Subsystem Readiness Probes")
            for sub, is_ready in checks.items():
                icon = "🟢" if is_ready else "🔴"
                st.markdown(f"- {icon} **{sub.replace('_', ' ').title()}**: `{'Ready' if is_ready else 'Unready / Standby'}`")

        with s2:
            st.markdown("#### Persistent Storage Status")
            gdrive_conn = storage_meta.get("google_drive_connected", False)
            gdrive_root = storage_meta.get("google_drive_root", "N/A")
            free_disk = storage_meta.get("local_free_disk_gb", "N/A")
            budget_mb = storage_meta.get("storage_budget_mb", "N/A")

            st.markdown(f"- **Google Drive Connected**: {'🟢 Yes' if gdrive_conn else '🔴 No'}")
            st.markdown(f"- **Google Drive Root**: `{gdrive_root}`")
            st.markdown(f"- **Local Free Disk**: `{free_disk} GB`")
            st.markdown(f"- **Local Storage Budget**: `{budget_mb} MB`")
            st.markdown(f"- **ChromaDB Collection**: `{vector_meta.get('collection_name', 'N/A')}`")

    except APIConnectionError:
        st.error(
            f"🔌 **Backend Offline**: Unable to connect to `{api_client.base_url}`. "
            "Please start the FastAPI service to inspect live knowledge-base status."
        )
    except APIClientError as e:
        st.error(f"❌ API Diagnostic Error: {str(e)}")
