"""Page E: About, System Architecture & Operational Diagnostics View.

Provides an architectural overview of the Customer Support Intelligence Assistant,
explaining Multi-Contextual Prompting, hybrid dense-sparse retrieval,
citation validation, and deployment limits.
"""

from typing import Dict, Any
import streamlit as st

from frontend.api_client import APIClient, APIClientError


def render_about_view(api_client: APIClient) -> None:
    """Render architecture documentation and system diagnostics."""
    st.markdown("## ℹ️ System Architecture & Engineering Principles")
    st.markdown(
        "The **ApexPrint Customer Support Intelligence Assistant** is an enterprise-grade "
        "Retrieval-Augmented Generation (RAG) platform incorporating **Multi-Contextual Prompting (MCP)**, "
        "hybrid sparse-dense retrieval, and automated citation validation."
    )

    # Tabs for structured explanation
    t_arch, t_mcp, t_retrieval, t_validation, t_storage = st.tabs([
        "🏗️ Architecture Overview",
        "🔀 Multi-Contextual Prompting",
        "🔍 Hybrid Retrieval & RRF",
        "🛡️ Citation Validation",
        "☁️ Storage & Resource Limits",
    ])

    with t_arch:
        st.markdown(
            """
            ### End-to-End System Flow
            The system accepts natural-language customer inquiries, routes intent across functional support categories,
            retrieves corroborating passages using hybrid semantic and lexical search, and synthesizes answers
            with strictly grounded source citations.

            ```
            [ Customer Inquiry ]
                    │
                    ▼
            [ Category Router / Intent Analyzer ]
                    │
            ┌───────┴───────────────────────┐
            ▼                               ▼
            [ Dense Vector Search ]        [ BM25 Lexical Keyword Search ]
            (all-MiniLM-L6-v2 + ChromaDB)  (Rank-BM25 with tokenization)
                    │                               │
                    └───────┬───────────────────────┘
                            ▼
                    [ Reciprocal Rank Fusion (RRF) ]
                            │
                            ▼
                    [ Multi-Context Prompt Assembly ]
                    (Balanced cross-category context)
                            │
                            ▼
                    [ LLM Synthesis (Mistral-7B) ]
                            │
                            ▼
                    [ Citation Groundedness Verification ]
                            │
                            ▼
            [ Verified Response + Grounded Citations ]
            ```
            """
        )

    with t_mcp:
        st.markdown(
            """
            ### Multi-Contextual Prompting (MCP)
            Standard RAG systems rely on single-channel semantic similarity, often retrieving homogeneous
            passages that fail to resolve complex multi-part customer inquiries (e.g. troubleshooting an error
            while simultaneously verifying warranty eligibility).

            **MCP solves this by:**
            1. **Intent Analysis**: Identifying all relevant categories (`troubleshooting`, `warranty`, `product_manual`, `faq`).
            2. **Targeted Sub-Queries**: Querying each category partition independently to guarantee diversity.
            3. **Balanced Prompt Contexts**: Structuring context blocks by category tag, preventing one category from crowding out another.
            4. **Reduced Hallucinations**: Constraining generation strictly to assembled category blocks.
            """
        )

    with t_retrieval:
        st.markdown(
            """
            ### Hybrid Dense + Sparse Retrieval (RRF)
            Combining dense semantic embeddings with BM25 keyword matching eliminates typical RAG failure modes
            such as exact product SKU mismatches or vocabulary divergence.

            - **Dense Channel**: `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional embeddings stored in ChromaDB.
            - **Sparse Channel**: Tokenized BM25 with lowercase filtering and stopword handling.
            - **Rank Fusion**: Reciprocal Rank Fusion (RRF) with constant `k = 60`:
            $$RRF(d) = \\sum_{m \\in M} \\frac{1}{60 + r_m(d)}$$
            """
        )

    with t_validation:
        st.markdown(
            """
            ### Automated Citation Groundedness Validation
            To enforce high enterprise reliability and eliminate ungrounded hallucinations:
            - **Post-Generation Verification**: Every citation emitted in `[Source: document, Page X]` format is parsed and checked against the retrieved evidence text chunks.
            - **N-gram Containment & Fuzzy Matching**: Verifies that claimed facts appear verbatim or near-verbatim in the retrieved source.
            - **Strict Fallback**: If evidence is insufficient, the system tags `evidence_status: INSUFFICIENT` rather than fabricating an answer.
            """
        )

    with t_storage:
        st.markdown(
            """
            ### Strict Storage Policy & Cost Governance
            - **Google Drive Primary Persistence**: All document archives, ChromaDB snapshots, and backup zips reside on Google Drive (`G:\\My Drive\\Internship_RAG_MCP_Capstone`).
            - **Minimal Local Storage**: Local workspace incremental footprint is strictly capped under 1 GB (currently < 20 MB).
            - **Remote GPU Compute**: Heavy LLM generation is hosted on Google Colab GPU nodes (Mistral-7B-Instruct-v0.3), consuming zero local model checkpoint storage.
            - **Transparent State Reporting**: When remote inference is on standby, the system explicitly reports `READY_FOR_COLAB_INFERENCE` or `TEST_MOCK_MODE` without misleading the user.
            """
        )

    # Subsystem Diagnostic Snapshot
    st.divider()
    st.markdown("### 🖥️ Live Backend Runtime Diagnostics")
    try:
        health = api_client.get_health()
        col1, col2 = st.columns(2)
        with col1:
            st.json(health.get("storage", {}))
        with col2:
            st.json(health.get("compute", {}))
    except Exception as e:
        st.warning(f"Backend diagnostics currently unavailable: {str(e)}")
