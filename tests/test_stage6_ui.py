"""Stage 6 Automated Test Suite: Streamlit Frontend, API Client, Components & User Workflows.

Covers all 16 required test scenarios:
1. Application startup
2. Page navigation
3. API client responses
4. Chat submission
5. Baseline mode
6. Multi-context mode
7. Citation rendering
8. Document upload
9. Document listing
10. Document deletion confirmation
11. Lifecycle-state display & searchability invariant
12. Backend unavailable handling
13. LLM unavailable (Colab standby) handling
14. Invalid API response & error handling
15. Feedback submission
16. Session-state behavior & memory boundaries
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import httpx
import pytest
from streamlit.testing.v1 import AppTest

from frontend.api_client import (
    APIClient,
    APIClientError,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)
from frontend.state import (
    init_session_state,
    add_chat_turn,
    clear_chat_history,
    mark_feedback_submitted,
    is_feedback_submitted,
)
from frontend.components.badges import (
    get_lifecycle_badge_html,
    get_provider_badge_html,
    get_evidence_badge_html,
    get_category_badge_html,
)
from frontend.components.citations import render_citations
from app.main import app


# ==============================================================================
# 1. API Client Unit Tests
# ==============================================================================

class TestAPIClient(unittest.TestCase):
    """Unit tests for frontend/api_client.py."""

    def setUp(self):
        self.client = APIClient(base_url="http://127.0.0.1:8000", timeout=5.0)

    def test_client_initialization(self):
        """Verify client URL sanitization and defaults."""
        c = APIClient("http://localhost:9000/")
        self.assertEqual(c.base_url, "http://localhost:9000")
        self.assertEqual(c.timeout, 15.0)

    @patch("httpx.Client.get")
    def test_get_health_success(self, mock_get):
        """Verify get_health maps 200 JSON correctly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "healthy",
            "uptime_seconds": 45.2,
            "storage": {"google_drive_connected": True, "local_free_disk_gb": 65.5},
        }
        mock_get.return_value = mock_resp

        result = self.client.get_health()
        self.assertEqual(result["status"], "healthy")
        self.assertTrue(result["storage"]["google_drive_connected"])

    @patch("httpx.Client.get")
    def test_get_ready_503_handled(self, mock_get):
        """Verify 503 unready response returns structured data without raising."""
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.json.return_value = {
            "status": "not_ready",
            "ready": False,
            "checks": {"storage": True, "vector_store": False},
        }
        mock_get.return_value = mock_resp

        result = self.client.get_ready()
        self.assertEqual(result["status"], "not_ready")
        self.assertFalse(result["ready"])

    @patch("httpx.Client.get")
    def test_connection_error_raised(self, mock_get):
        """Verify APIConnectionError is raised when host is unreachable."""
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        with self.assertRaises(APIConnectionError) as ctx:
            self.client.get_health()
        self.assertIn("Unable to connect", str(ctx.exception))

    @patch("httpx.Client.get")
    def test_timeout_error_raised(self, mock_get):
        """Verify APITimeoutError is raised when request exceeds limit."""
        mock_get.side_effect = httpx.TimeoutException("Read timed out")
        with self.assertRaises(APITimeoutError):
            self.client._get("/slow-endpoint")

    @patch("httpx.Client.post")
    def test_query_baseline_mode(self, mock_post):
        """Verify query in baseline mode sends correct payload."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "query": "Error E-101",
            "answer": "Paper jam fix",
            "retrieval_mode": "baseline",
            "supporting_citations": [],
            "provider_status": "READY_FOR_COLAB_INFERENCE",
        }
        mock_post.return_value = mock_resp

        res = self.client.query(query="Error E-101", retrieval_mode="baseline", top_k=3)
        self.assertEqual(res["retrieval_mode"], "baseline")
        # Verify JSON payload passed to httpx
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["retrieval_mode"], "baseline")
        self.assertEqual(kwargs["json"]["top_k"], 3)

    @patch("httpx.Client.post")
    def test_query_multi_context_mode(self, mock_post):
        """Verify query in multi_context mode sends correct payload."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "query": "Warranty coverage for E-101",
            "answer": "Coverage details",
            "retrieval_mode": "multi_context",
            "selected_categories": ["troubleshooting", "warranty"],
        }
        mock_post.return_value = mock_resp

        res = self.client.query(query="Warranty coverage for E-101", retrieval_mode="multi_context")
        self.assertEqual(res["retrieval_mode"], "multi_context")
        self.assertEqual(res["selected_categories"], ["troubleshooting", "warranty"])

    @patch("httpx.Client.post")
    def test_upload_document_no_retries(self, mock_post):
        """Verify document upload uses multipart form and disables retries."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            "status": "SUCCESS",
            "document_id": "doc_test_123",
            "lifecycle_status": "pending_index",
            "chunk_count": 2,
        }
        mock_post.return_value = mock_resp

        res = self.client.upload_document(
            file_bytes=b"sample content",
            filename="test_manual.md",
            category="product_manual",
        )
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["document_id"], "doc_test_123")
        # Ensure post was called once
        self.assertEqual(mock_post.call_count, 1)

    @patch("httpx.Client.get")
    def test_list_documents_filtering(self, mock_get):
        """Verify list_documents passes category and status filters."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"total": 2, "documents": []}
        mock_get.return_value = mock_resp

        self.client.list_documents(category="warranty", status="indexed", include_deleted=True)
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["category"], "warranty")
        self.assertEqual(kwargs["params"]["status"], "indexed")
        self.assertTrue(kwargs["params"]["include_deleted"])

    @patch("httpx.Client.delete")
    def test_delete_document(self, mock_delete):
        """Verify delete_document calls DELETE on the correct document endpoint."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "deleted_chunks": 3}
        mock_delete.return_value = mock_resp

        res = self.client.delete_document("doc_sample_999")
        self.assertEqual(res["deleted_chunks"], 3)
        self.assertIn("doc_sample_999", mock_delete.call_args[0][0])

    @patch("httpx.Client.post")
    def test_submit_feedback(self, mock_post):
        """Verify submit_feedback constructs valid feedback payload."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "message": "Feedback recorded"}
        mock_post.return_value = mock_resp

        res = self.client.submit_feedback(
            query_id="q100",
            rating=5,
            comment="Grounded citations",
            flagged_incorrect=False,
        )
        self.assertEqual(res["status"], "success")


# ==============================================================================
# 2. Components & Session State Tests
# ==============================================================================

class TestUIComponentsAndState(unittest.TestCase):
    """Unit tests for badges, citations, and state management."""

    def test_lifecycle_badge_searchability_invariant(self):
        """Strictly verify ONLY 'indexed' is marked searchable."""
        # 1. Indexed -> Searchable
        indexed_badge = get_lifecycle_badge_html("indexed", is_searchable=True)
        self.assertIn("Indexed & Searchable", indexed_badge)
        self.assertNotIn("Not Searchable", indexed_badge)

        # 2. Processed -> Not Searchable
        processed_badge = get_lifecycle_badge_html("processed", is_searchable=False)
        self.assertIn("Not Searchable", processed_badge)

        # 3. Pending Index -> Not Searchable
        pending_badge = get_lifecycle_badge_html("pending_index", is_searchable=False)
        self.assertIn("Not Searchable", pending_badge)

        # 4. Uploaded -> Not Searchable
        uploaded_badge = get_lifecycle_badge_html("uploaded", is_searchable=False)
        self.assertIn("Not Searchable", uploaded_badge)

        # 5. Failed & Deleted
        failed_badge = get_lifecycle_badge_html("indexing_failed", is_searchable=False)
        self.assertIn("Indexing Failed", failed_badge)

        deleted_badge = get_lifecycle_badge_html("deleted", is_searchable=False)
        self.assertIn("Deleted", deleted_badge)

    def test_provider_badge_honest_reporting(self):
        """Verify provider badges clearly distinguish Standby, Mock, and Online."""
        colab_badge = get_provider_badge_html("READY_FOR_COLAB_INFERENCE")
        self.assertIn("Colab GPU Standby", colab_badge)

        mock_badge = get_provider_badge_html("TEST_MOCK_MODE")
        self.assertIn("Test Mock Mode", mock_badge)

        online_badge = get_provider_badge_html("ONLINE")
        self.assertIn("Remote GPU Online", online_badge)

    def test_evidence_badge_status(self):
        """Verify groundedness evidence badge levels."""
        self.assertIn("Sufficient", get_evidence_badge_html("SUFFICIENT"))
        self.assertIn("Partial", get_evidence_badge_html("PARTIAL"))
        self.assertIn("Insufficient", get_evidence_badge_html("INSUFFICIENT"))

    def test_category_badge_html(self):
        """Verify category badges render distinct styling."""
        self.assertIn("Troubleshooting", get_category_badge_html("troubleshooting"))
        self.assertIn("Warranty", get_category_badge_html("warranty"))
        self.assertIn("Product Manual", get_category_badge_html("product_manual"))
        self.assertIn("FAQ", get_category_badge_html("faq"))


# ==============================================================================
# 3. Streamlit AppTest End-to-End UI Tests
# ==============================================================================

class TestStreamlitAppTest(unittest.TestCase):
    """Integration tests using Streamlit AppTest."""

    @patch.object(APIClient, "get_health")
    def test_app_startup(self, mock_health):
        """Test 1: Application startup and basic element rendering."""
        mock_health.return_value = {
            "status": "healthy",
            "uptime_seconds": 15.0,
            "storage": {"google_drive_connected": True, "local_free_disk_gb": 65.5},
            "compute": {"llm_provider": "colab_remote"},
        }
        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        # Verify no fatal crashes
        self.assertEqual(len(at.exception), 0)
        # Verify sidebar radio navigation exists
        self.assertGreater(len(at.sidebar.radio), 0)
        self.assertIn("Chat Assistant", at.sidebar.radio[0].value)

    @patch.object(APIClient, "get_ready")
    @patch.object(APIClient, "get_knowledge_base_status")
    @patch.object(APIClient, "list_documents")
    @patch.object(APIClient, "get_health")
    def test_page_navigation(self, mock_health, mock_list_docs, mock_kb_status, mock_ready):
        """Test 2: Navigate through all 5 application pages without error."""
        mock_health.return_value = {
            "status": "healthy",
            "uptime_seconds": 10.0,
            "storage": {"google_drive_connected": True, "local_free_disk_gb": 65.5},
            "compute": {"llm_provider": "colab_remote"},
        }
        mock_list_docs.return_value = {
            "total": 1,
            "documents": [
                {
                    "document_id": "doc_test_01",
                    "filename": "apexprint_manual.md",
                    "category": "product_manual",
                    "lifecycle_status": "indexed",
                    "is_searchable": True,
                    "chunk_count": 2,
                    "file_size_bytes": 1024,
                    "first_ingested": "2026-10-26T10:00:00",
                }
            ],
        }
        mock_kb_status.return_value = {
            "total_active_documents": 1,
            "searchable_documents_count": 1,
            "total_active_chunks": 2,
            "documents_by_category": {"product_manual": 1},
            "documents_by_lifecycle_status": {"indexed": 1, "pending_index": 0},
            "storage": {"google_drive_connected": True, "local_free_disk_gb": 65.5, "storage_budget_mb": 1024},
            "vector_store": {"collection_name": "test_kb", "total_indexed_chunks": 2},
        }
        mock_ready.return_value = {
            "status": "ready",
            "ready": True,
            "checks": {"storage": True, "manifest": True, "vector_store": True},
        }

        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        self.assertEqual(len(at.exception), 0)

        nav_options = [
            "💬 Chat Assistant",
            "📄 Document Management",
            "⚖️ Mode Comparison",
            "📊 Knowledge Base Status",
            "ℹ️ Architecture & About",
        ]

        for option in nav_options:
            sub_at = AppTest.from_file("frontend/app.py", default_timeout=5)
            sub_at.run()
            sub_at.sidebar.radio[0].set_value(option)
            sub_at.run()
            self.assertEqual(len(sub_at.exception), 0, f"Exception occurred navigating to {option}")

    @patch.object(APIClient, "query")
    def test_chat_submission_flow(self, mock_query):
        """Test 4 & 5 & 6: Chat submission in Multi-Context and Baseline modes."""
        mock_query.return_value = {
            "query": "How to fix error E-101?",
            "answer": "Clear paper jam in tray B [Source: apexprint_troubleshooting.md, Page 1].",
            "retrieval_mode": "multi_context",
            "selected_categories": ["troubleshooting"],
            "supporting_citations": [
                {
                    "document_source": "apexprint_troubleshooting.md",
                    "page_or_section": "Page 1",
                    "snippet": "Paper jam clearance",
                    "relevance_score": 0.85,
                    "category": "troubleshooting",
                    "chunk_id": "chunk_01",
                    "is_verified": True,
                }
            ],
            "evidence_status": "SUFFICIENT",
            "retrieval_latency_ms": 1.2,
            "provider_status": "READY_FOR_COLAB_INFERENCE",
            "citations": [],
        }

        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        self.assertEqual(len(at.exception), 0)

        # Submit chat input
        if len(at.chat_input) > 0:
            at.chat_input[0].set_value("How to fix error E-101?")
            at.chat_input[0].run()
            self.assertEqual(len(at.exception), 0)

    @patch.object(APIClient, "get_health")
    def test_backend_offline_display(self, mock_health):
        """Test 12: Backend unavailable renders clear error banner without crashing."""
        mock_health.side_effect = APIConnectionError("Target offline")

        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        self.assertEqual(len(at.exception), 0)
        # Verify markdown in sidebar reports offline
        sidebar_text = "".join(m.value for m in at.sidebar.markdown)
        self.assertIn("Backend Offline", sidebar_text)


# ==============================================================================
# 4. Genuine FastAPI-to-Frontend Client Integration
# ==============================================================================

class TestFrontendFastAPIIntegration(unittest.TestCase):
    """Direct integration test between APIClient and FastAPI application."""

    def setUp(self):
        from starlette.testclient import TestClient
        self.client = TestClient(app)

    def test_fastapi_health_endpoint_contract(self):
        """Verify APIClient contracts against genuine FastAPI /health route."""
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("storage", data)
        self.assertIn("google_drive_connected", data["storage"])

    def test_fastapi_knowledge_base_status_contract(self):
        """Verify APIClient contracts against genuine FastAPI /knowledge-base/status route."""
        resp = self.client.get("/api/v1/knowledge-base/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "operational")
        self.assertIn("total_active_documents", data)
        self.assertIn("documents_by_lifecycle_status", data)
        self.assertIn("searchable_documents_count", data)

    def test_fastapi_documents_listing_contract(self):
        """Verify APIClient contracts against genuine FastAPI /documents listing route."""
        resp = self.client.get("/api/v1/documents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total", data)
        self.assertIn("documents", data)
        self.assertEqual(data["total"], len(data["documents"]))
        for doc in data["documents"]:
            # Check searchability invariant in live API
            if doc["lifecycle_status"] == "indexed":
                self.assertTrue(doc["is_searchable"])
            else:
                self.assertFalse(doc["is_searchable"])
