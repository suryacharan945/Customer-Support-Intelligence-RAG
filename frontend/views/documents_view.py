"""Page B: Document Lifecycle Management View.

Enables secure document ingestion, format checking, metadata inspection,
lifecycle tracking (6 states), and atomic deletion.
Strictly adheres to:
- Searchability invariant: Only 'indexed' documents are searchable.
- Explicit indexing-pending notifications.
- Confirmed atomic deletion.
- Zero local database modification (all operations route through FastAPI).
"""

from typing import Dict, Any, List, Optional
import streamlit as st

from frontend.api_client import APIClient, APIClientError, APIConnectionError
from frontend.components.badges import (
    get_lifecycle_badge_html,
    get_category_badge_html,
)

CORE_DOCUMENT_FILENAMES = {
    "apexprint_colorwave850_user_manual.md",
    "apexprint_prox400_quick_start.pdf",
    "apexprint_ecotank_l3150_specs.txt",
    "apexprint_error_codes_and_hardware_troubleshooting.md",
    "apexprint_network_wifi_setup_guide.txt",
    "apexprint_limited_warranty_and_sla_policy.md",
    "apexprint_extended_care_replacement_terms.pdf",
    "apexprint_frequently_asked_questions.md",
    "apexprint_account_and_billing_faq.txt",
}


def render_documents_view(api_client: APIClient) -> None:
    """Render document management and lifecycle dashboard."""
    st.markdown("## 📄 Document Lifecycle Management")
    st.markdown(
        "Upload, inspect, and manage enterprise support documentation across the "
        "six-stage lifecycle state machine. **Searchability is strictly gated until vector indexing is complete.**"
    )

    tab_list, tab_upload = st.tabs(["📚 Ingested Knowledge Base", "📤 Ingest New Document"])

    # --------------------------------------------------------------------------
    # Tab 1: Ingested Knowledge Base
    # --------------------------------------------------------------------------
    with tab_list:
        # Filters
        fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 2, 1])

        with fcol1:
            cat_filter = st.selectbox(
                "Filter by Category",
                options=["all", "product_manual", "troubleshooting", "warranty", "faq"],
                index=0,
                key="doc_cat_filter",
            )
        with fcol2:
            status_filter = st.selectbox(
                "Filter by Lifecycle Status",
                options=["all", "indexed", "pending_index", "processed", "uploaded", "indexing_failed", "deleted"],
                index=0,
                key="doc_status_filter",
            )
        with fcol3:
            include_deleted = st.checkbox("Include Deleted Documents", value=False, key="inc_del_chk")

        with fcol4:
            st.write("")
            refresh_btn = st.button("🔄 Refresh", key="btn_refresh_docs")

        # Fetch documents
        try:
            doc_data = api_client.list_documents(
                category=cat_filter if cat_filter != "all" else None,
                status=status_filter if status_filter != "all" else None,
                include_deleted=include_deleted,
            )
            documents: List[Dict[str, Any]] = doc_data.get("documents", [])
            total_count = doc_data.get("total", len(documents))

            st.caption(f"Showing **{len(documents)}** of **{total_count}** documents")

            if not documents:
                st.info("No documents match the current filter criteria.")
            else:
                for doc in documents:
                    doc_id = doc.get("document_id", "")
                    filename = doc.get("filename", "unknown")
                    category = doc.get("category", "general")
                    lifecycle_st = doc.get("lifecycle_status", "uploaded")
                    is_searchable = doc.get("is_searchable", False)
                    chunks = doc.get("chunk_count", 0)
                    size_bytes = doc.get("file_size_bytes", 0)
                    ingested_at = doc.get("first_ingested", "N/A")
                    is_core = filename in CORE_DOCUMENT_FILENAMES

                    badge_html = get_lifecycle_badge_html(lifecycle_st, is_searchable)
                    cat_html = get_category_badge_html(category)
                    core_tag = '<span style="color:#6366f1; font-weight:600; font-size:11px;">[Core Benchmark]</span> ' if is_core else ''

                    with st.expander(f"{core_tag}{filename} ({category})", expanded=False):
                        c1, c2, c3 = st.columns([2, 2, 2])
                        with c1:
                            st.markdown(f"**Document ID**: `{doc_id}`")
                            st.markdown(f"**Category**: {cat_html}", unsafe_allow_html=True)
                            st.markdown(f"**Lifecycle State**: {badge_html}", unsafe_allow_html=True)

                        with c2:
                            st.markdown(f"**Chunks Generated**: `{chunks}`")
                            st.markdown(f"**File Size**: `{size_bytes:,} bytes`")
                            st.markdown(f"**Searchable in RAG?**: {'✅ **Yes**' if is_searchable else '❌ **No (Pending Index)**'}")

                        with c3:
                            st.markdown(f"**Ingested Date**: `{ingested_at[:19] if len(ingested_at) >= 19 else ingested_at}`")
                            if not is_searchable and lifecycle_st in ("pending_index", "processed", "uploaded"):
                                st.warning("⏳ Document processed but pending vector database indexing. Chunks are not yet searchable.")

                        # Action bar for this document
                        st.divider()
                        del_col1, del_col2 = st.columns([3, 1])
                        with del_col1:
                            confirm_box = st.checkbox(
                                f"Confirm permanent deletion of `{filename}`",
                                key=f"confirm_del_{doc_id}",
                            )
                        with del_col2:
                            delete_btn = st.button(
                                "🗑️ Delete",
                                key=f"btn_del_{doc_id}",
                                disabled=not confirm_box,
                                help="Permanently delete from storage, ChromaDB, and BM25 index",
                            )

                        if delete_btn and confirm_box:
                            if is_core:
                                st.error("🛑 Deletion Protected: Authoritative baseline documents cannot be deleted during UI testing.")
                            else:
                                with st.spinner(f"Deleting document {doc_id}..."):
                                    try:
                                        del_res = api_client.delete_document(doc_id)
                                        st.success(f"✅ Document `{filename}` successfully purged! ({del_res.get('deleted_chunks', 0)} chunks removed)")
                                        st.rerun()
                                    except APIClientError as e:
                                        st.error(f"Deletion failed: {str(e)}")

        except APIConnectionError:
            st.error(f"🔌 Backend Offline: Unable to connect to `{api_client.base_url}`.")
        except APIClientError as e:
            st.error(f"API Error fetching documents: {str(e)}")

    # --------------------------------------------------------------------------
    # Tab 2: Ingest New Document
    # --------------------------------------------------------------------------
    with tab_upload:
        st.markdown("### 📤 Upload New Document to Knowledge Base")
        st.markdown(
            "Upload a **PDF**, **Markdown (.md)**, or **Text (.txt)** file to ingest into the knowledge base. "
            "Maximum file size: **10 MB**. The pipeline will validate, chunk, and register the document in the manifest."
        )

        col_up1, col_up2 = st.columns([2, 1])

        with col_up1:
            uploaded_file = st.file_uploader(
                "Choose support document file",
                type=["pdf", "md", "txt"],
                key="doc_uploader",
                help="Only .pdf, .md, and .txt files are supported. Max 10MB.",
            )

        with col_up2:
            target_category = st.selectbox(
                "Target Category",
                options=["troubleshooting", "warranty", "product_manual", "faq"],
                index=0,
                key="upload_category_select",
            )

        if uploaded_file is not None:
            # Client-side size validation
            file_bytes = uploaded_file.getvalue()
            size_mb = len(file_bytes) / (1024 * 1024)

            st.info(f"File: **{uploaded_file.name}** ({size_mb:.2f} MB, {target_category})")

            if size_mb > 10.0:
                st.error("❌ File exceeds 10 MB limit. Please select a smaller file.")
                return

            upload_button = st.button("🚀 Process & Ingest Document", key="btn_execute_upload")

            if upload_button:
                with st.spinner(f"Processing and chunking '{uploaded_file.name}'..."):
                    try:
                        result = api_client.upload_document(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name,
                            category=target_category,
                        )

                        doc_id = result.get("document_id", "unknown")
                        chunks = result.get("chunk_count", 0)
                        lifecycle = result.get("lifecycle_status", "pending_index")
                        is_searchable = result.get("is_searchable", False)

                        st.success(
                            f"✅ **Document Processed Successfully!**\n\n"
                            f"- **Document ID**: `{doc_id}`\n"
                            f"- **Filename**: `{uploaded_file.name}`\n"
                            f"- **Category**: `{target_category}`\n"
                            f"- **Chunks Created**: `{chunks}`\n"
                            f"- **Lifecycle Status**: `{lifecycle}`"
                        )

                        if not is_searchable:
                            st.warning(
                                "ℹ️ **Notice: Document is Pending Indexing.**\n"
                                "The document has been registered and chunked in the manifest, but its vector "
                                "embeddings will be upserted to ChromaDB during the next index synchronization. "
                                "It is **not yet searchable** in customer queries."
                            )

                    except APIClientError as e:
                        st.error(f"❌ Upload Failed: {str(e)}")
                    except Exception as e:
                        st.error(f"⚠️ Unexpected Upload Error: {str(e)}")
