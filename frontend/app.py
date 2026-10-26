"""Main Streamlit Application Entrypoint for ApexPrint Customer Support Intelligence Assistant.

Orchestrates sidebar navigation, global state initialization,
health probe telemetry, and modular view routing.
"""

import os
import streamlit as st

from frontend.state import init_session_state, clear_chat_history
from frontend.api_client import APIClient, APIConnectionError
from frontend.views.chat_view import render_chat_view
from frontend.views.documents_view import render_documents_view
from frontend.views.comparison_view import render_comparison_view
from frontend.views.knowledge_base_view import render_knowledge_base_view
from frontend.views.about_view import render_about_view


# Page configuration
st.set_page_config(
    page_title="ApexPrint Support Intelligence Assistant",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
init_session_state()

# Inject custom CSS for clean enterprise aesthetics
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stSidebarHeader"] {
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    """Main application loop."""
    # Sidebar: Title & Branding
    st.sidebar.markdown(
        """
        <div style="text-align: center; margin-bottom: 12px;">
            <h2 style="margin: 0; color: #1e3a8a;">🖨️ ApexPrint</h2>
            <p style="margin: 2px 0 0 0; font-size: 13px; color: #64748b; font-weight: 500;">
                Customer Support Intelligence
            </p>
            <span style="font-size: 11px; background-color: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 10px; font-weight: 600;">
                Multi-Context RAG + MCP
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API Client instantiation
    api_url = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
    api_client = APIClient(base_url=api_url, timeout=15.0)

    # Sidebar: Backend Connectivity Probe
    st.sidebar.markdown("---")
    try:
        health_data = api_client.get_health()
        gdrive_on = health_data.get("storage", {}).get("google_drive_connected", False)
        free_gb = health_data.get("storage", {}).get("local_free_disk_gb", "N/A")
        
        st.sidebar.markdown(
            f"""
            <div style="background-color: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; padding: 8px 10px; font-size: 12px; margin-bottom: 10px;">
                <div style="color: #15803d; font-weight: 600;">🟢 Backend Online</div>
                <div style="color: #4b5563; font-size: 11px; margin-top: 2px;">
                    Uptime: {health_data.get('uptime_seconds', 0):.0f}s • Free Disk: {free_gb} GB<br/>
                    Drive Sync: {'Connected' if gdrive_on else 'Standby'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except APIConnectionError:
        st.sidebar.markdown(
            f"""
            <div style="background-color: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; padding: 8px 10px; font-size: 12px; margin-bottom: 10px;">
                <div style="color: #b91c1c; font-weight: 600;">🔴 Backend Offline</div>
                <div style="color: #6b7280; font-size: 11px; margin-top: 2px;">
                    Target: {api_url}<br/>
                    Start FastAPI to enable live querying.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.sidebar.warning("Backend status probe unready.")

    # Check if page was specified in URL query params for deep-linking
    query_page = st.query_params.get("page", "")
    default_nav_idx = 0
    nav_options = [
        "💬 Chat Assistant",
        "📄 Document Management",
        "⚖️ Mode Comparison",
        "📊 Knowledge Base Status",
        "ℹ️ Architecture & About",
    ]
    if query_page:
        for idx, opt in enumerate(nav_options):
            if query_page.lower() in opt.lower():
                default_nav_idx = idx
                break

    # Sidebar Navigation
    page = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=default_nav_idx,
        key="main_navigation_radio",
    )

    st.sidebar.markdown("---")

    # Sidebar Quick Actions
    if st.sidebar.button("🧹 Clear Conversation", key="sb_clear_chat", use_container_width=True):
        clear_chat_history()
        st.rerun()

    # Advanced Settings Expander
    with st.sidebar.expander("⚙️ Connection Settings", expanded=False):
        custom_url = st.text_input("FastAPI Base URL", value=api_url, key="custom_api_url")
        if custom_url != api_url:
            os.environ["FASTAPI_BASE_URL"] = custom_url
            st.rerun()

    # Footer
    st.sidebar.markdown(
        """
        <div style="position: fixed; bottom: 10px; font-size: 11px; color: #9ca3af; text-align: center;">
            Internship RAG Capstone • Stage 6
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Route to Selected View
    if "Chat Assistant" in page:
        render_chat_view(api_client)
    elif "Document Management" in page:
        render_documents_view(api_client)
    elif "Mode Comparison" in page:
        render_comparison_view(api_client)
    elif "Knowledge Base Status" in page:
        render_knowledge_base_view(api_client)
    elif "Architecture" in page:
        render_about_view(api_client)


main()
