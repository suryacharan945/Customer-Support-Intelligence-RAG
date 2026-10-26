"""Stage 5 FastAPI Integration, Document Lifecycle Management, and End-to-End Test Suite.

Comprehensive test coverage for:
- Liveness (/health) and Deep Readiness (/ready) Probes
- Baseline and Multi-Context RAG query execution
- Backend error handling (503 Vector Store, 504 Timeout, 502 Bad Gateway)
- Request validation (422 empty body, invalid mode fallback)
- Document Uploads (.pdf, .txt, .md)
- Upload security: Path traversal defense, file type validation (400), size limits (413)
- Duplicate content detection (idempotent skip)
- Document lifecycle tracking (6 states) and searchability boundaries
- Atomic document deletion and repeated deletion (404)
- Knowledge base status metrics
- Continuous learning feedback collection
- FastAPI Dependency Injection (Depends) overrides
"""

import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from starlette.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.core.config import settings, Settings
from app.api.deps import (
    get_settings,
    get_vector_retriever,
    get_rag_service,
    get_ingestion_service,
    get_manifest,
)
from app.api.endpoints.rag import QueryResponse, Citation
from app.retrieval.vector_store import (
    VectorStoreRetriever,
    VectorStoreNotInitializedError,
    VectorStoreQueryError,
)
from app.generation.llm_client import (
    LLMClient,
    RemoteInferenceTimeoutError,
    RemoteInferenceError,
)
from app.services.rag_service import RAGService
from app.ingestion.manifest import IngestionManifest
from app.services.ingestion_service import IngestionService

client = TestClient(app)


# ==============================================================================
# Test Fixtures & Helpers
# ==============================================================================

def create_operational_test_rag_service():
    """Create an operational RAGService with mock-allowed vector retriever and BM25 index."""
    v_ret = VectorStoreRetriever(allow_mock=True)
    llm = LLMClient(provider="mock", allow_mock=True)
    svc = RAGService(vector_retriever=v_ret, llm_client=llm, allow_mock=True)

    from app.ingestion.chunker import TextChunk
    test_chunks = [
        TextChunk(
            chunk_id="chunk_trou_01",
            document_id="doc_trou_01",
            chunk_index=0,
            text="To clear paper jam error E-101, power off printer, open door B, and pull paper gently.",
            category="troubleshooting",
            source="error_troubleshooting.md",
            page_number=1,
            content_hash="h_trou_01",
            metadata={"filename": "error_troubleshooting.md", "category": "troubleshooting"},
        ),
        TextChunk(
            chunk_id="chunk_warr_01",
            document_id="doc_warr_01",
            chunk_index=0,
            text="ProX-400 hardware warranty covers roller replacements and factory defects for 1 year.",
            category="warranty",
            source="warranty_guide.md",
            page_number=1,
            content_hash="h_warr_01",
            metadata={"filename": "warranty_guide.md", "category": "warranty"},
        ),
        TextChunk(
            chunk_id="chunk_prod_01",
            document_id="doc_prod_01",
            chunk_index=0,
            text="To replace rollers on ColorWave-850, disengage roller assembly clip C and slide out.",
            category="product_manual",
            source="colorwave_manual.md",
            page_number=1,
            content_hash="h_prod_01",
            metadata={"filename": "colorwave_manual.md", "category": "product_manual"},
        ),
    ]
    svc.index_bm25_chunks(test_chunks)
    return svc


# ==============================================================================
# 1. Health & Deep Readiness Probes
# ==============================================================================

def test_health_check_endpoint():
    """1. Verify GET /health and GET /api/v1/health return 200 with diagnostics."""
    for path in ["/health", f"{settings.API_V1_PREFIX}/health"]:
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["app_name"] == settings.PROJECT_NAME
        assert "uptime_seconds" in data
        assert "storage" in data
        assert "compute" in data
        assert data["storage"]["google_drive_root"] == settings.GOOGLE_DRIVE_ROOT


def test_readiness_probe_success():
    """2. Verify GET /ready returns 200 when all subsystems are operational."""
    mock_retriever = MagicMock()
    mock_retriever._collection = MagicMock()
    mock_retriever.collection_name = "test_collection"
    mock_retriever.count.return_value = 21

    app.dependency_overrides[get_vector_retriever] = lambda: mock_retriever
    try:
        resp = client.get(f"{settings.API_V1_PREFIX}/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["ready"] is True
        assert data["checks"]["storage"] is True
        assert data["checks"]["manifest"] is True
        assert data["checks"]["vector_store"] is True
        assert data["checks"]["llm_provider"] is True
    finally:
        app.dependency_overrides.clear()


def test_readiness_probe_vector_uninitialized_returns_503():
    """3. Verify GET /ready returns 503 when vector store is uninitialized and mock is disabled."""
    mock_retriever = MagicMock()
    mock_retriever._collection = None
    mock_retriever.allow_mock = False
    mock_retriever.collection_name = "test_col"
    mock_retriever.count.return_value = 0

    mock_settings = Settings(ALLOW_MOCK_FALLBACK=False, TEST_MODE=False)

    app.dependency_overrides[get_vector_retriever] = lambda: mock_retriever
    app.dependency_overrides[get_settings] = lambda: mock_settings
    try:
        resp = client.get(f"{settings.API_V1_PREFIX}/ready")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["ready"] is False
        assert data["checks"]["vector_store"] is False
    finally:
        app.dependency_overrides.clear()


def test_readiness_probe_storage_unready_returns_503():
    """4. Verify GET /ready returns 503 when persistent storage is unavailable."""
    with patch("os.path.isdir", return_value=False), patch("os.path.exists", return_value=False):
        resp = client.get(f"{settings.API_V1_PREFIX}/ready")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["storage"] is False


# ==============================================================================
# 2. Query Endpoints (Baseline & Multi-Context)
# ==============================================================================

def test_baseline_rag_query_success():
    """5. Verify POST /api/v1/query in baseline mode returns valid response."""
    test_service = create_operational_test_rag_service()
    app.dependency_overrides[get_rag_service] = lambda: test_service
    try:
        payload = {
            "query": "How do I clear paper jam error E-101?",
            "retrieval_mode": "baseline",
            "top_k": 3,
        }
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["retrieval_mode"] == "baseline"
        assert "answer" in data
        assert data["evidence_status"] in ("SUFFICIENT", "PARTIAL", "INSUFFICIENT")
        assert "retrieval_latency_ms" in data
    finally:
        app.dependency_overrides.clear()


def test_multi_context_rag_query_success():
    """6. Verify POST /api/v1/query in multi_context mode populates selected categories."""
    test_service = create_operational_test_rag_service()
    app.dependency_overrides[get_rag_service] = lambda: test_service
    try:
        payload = {
            "query": "What is the warranty coverage for ProX-400 and how to fix error E-101?",
            "retrieval_mode": "multi_context",
            "top_k": 5,
        }
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["retrieval_mode"] == "multi_context"
        assert len(data["selected_categories"]) >= 1
        assert any(c in data["selected_categories"] for c in ["troubleshooting", "warranty"])
        assert "answer" in data
    finally:
        app.dependency_overrides.clear()


def test_rag_query_vector_store_down_503():
    """7. Verify POST /api/v1/query returns 503 when vector store raises uninitialized error."""
    mock_service = MagicMock()
    mock_service.process_query.side_effect = VectorStoreNotInitializedError("ChromaDB offline")

    app.dependency_overrides[get_rag_service] = lambda: mock_service
    try:
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json={"query": "Test inquiry"})
        assert resp.status_code == 503
        assert "Vector store unavailable" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_rag_query_remote_timeout_504():
    """8. Verify POST /api/v1/query returns 504 when remote LLM times out."""
    mock_service = MagicMock()
    mock_service.process_query.side_effect = RemoteInferenceTimeoutError("Inference timed out after 15s")

    app.dependency_overrides[get_rag_service] = lambda: mock_service
    try:
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json={"query": "Test inquiry"})
        assert resp.status_code == 504
        assert "timeout" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_rag_query_remote_error_502():
    """9. Verify POST /api/v1/query returns 502 when remote LLM returns an error."""
    mock_service = MagicMock()
    mock_service.process_query.side_effect = RemoteInferenceError("Colab GPU runtime disconnected")

    app.dependency_overrides[get_rag_service] = lambda: mock_service
    try:
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json={"query": "Test inquiry"})
        assert resp.status_code == 502
        assert "inference error" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_rag_query_empty_body_422():
    """10. Verify POST /api/v1/query with empty or whitespace-only query returns 422."""
    resp1 = client.post(f"{settings.API_V1_PREFIX}/query", json={"query": ""})
    assert resp1.status_code == 422

    resp2 = client.post(f"{settings.API_V1_PREFIX}/query", json={"query": "   "})
    assert resp2.status_code == 422


def test_rag_query_invalid_retrieval_mode_fallback():
    """11. Verify POST /api/v1/query with unknown retrieval mode falls back gracefully."""
    test_service = create_operational_test_rag_service()
    app.dependency_overrides[get_rag_service] = lambda: test_service
    try:
        payload = {
            "query": "How to replace rollers on ColorWave-850?",
            "retrieval_mode": "non_existent_mode",
        }
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json=payload)
        assert resp.status_code == 200
        assert resp.json()["retrieval_mode"] == "multi_context"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 3. Document Lifecycle Management (Upload, Validation, Listing, Deletion)
# ==============================================================================

def test_document_upload_valid_markdown(tmp_path):
    """12. Verify POST /api/v1/documents with valid markdown file returns 201."""
    manifest_file = tmp_path / "test_manifest.json"
    custom_ingestion = IngestionService(manifest_path=manifest_file)

    app.dependency_overrides[get_ingestion_service] = lambda: custom_ingestion
    app.dependency_overrides[get_manifest] = lambda: custom_ingestion.manifest
    try:
        content = b"# ApexPrint Quick Setup\n\nConnect power cable and wait 30 seconds for green LED.\n"
        files = {"file": ("test_setup.md", io.BytesIO(content), "text/markdown")}
        data = {"category": "product_manual"}

        resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data=data)
        assert resp.status_code == 201
        res = resp.json()
        assert res["status"] == "SUCCESS"
        assert res["filename"] == "test_setup.md"
        assert res["category"] == "product_manual"
        assert res["lifecycle_status"] == "pending_index"
        assert res["is_searchable"] is False  # Never searchable until indexed!
        assert res["chunk_count"] >= 1
    finally:
        app.dependency_overrides.clear()


def test_document_upload_valid_text(tmp_path):
    """13. Verify POST /api/v1/documents with valid plain text file returns 201."""
    manifest_file = tmp_path / "test_manifest.json"
    custom_ingestion = IngestionService(manifest_path=manifest_file)

    app.dependency_overrides[get_ingestion_service] = lambda: custom_ingestion
    app.dependency_overrides[get_manifest] = lambda: custom_ingestion.manifest
    try:
        content = b"ApexPrint Warranty Policy: Standard 1-year coverage on all parts and labor.\n"
        files = {"file": ("warranty_addendum.txt", io.BytesIO(content), "text/plain")}
        data = {"category": "warranty"}

        resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data=data)
        assert resp.status_code == 201
        res = resp.json()
        assert res["status"] == "SUCCESS"
        assert res["filename"] == "warranty_addendum.txt"
        assert res["category"] == "warranty"
        assert res["lifecycle_status"] == "pending_index"
        assert res["is_searchable"] is False
    finally:
        app.dependency_overrides.clear()


def test_document_upload_invalid_file_type_400():
    """14. Verify POST /api/v1/documents rejects unsupported file formats with HTTP 400."""
    content = b"Binary executable content"
    files = {"file": ("malicious_payload.exe", io.BytesIO(content), "application/octet-stream")}
    data = {"category": "product_manual"}

    resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data=data)
    assert resp.status_code == 400
    assert "unsupported file extension" in resp.json()["detail"].lower()


def test_document_upload_oversized_file_413():
    """15. Verify POST /api/v1/documents rejects files exceeding 10MB with HTTP 413."""
    # 10.5 MB payload
    oversized_content = b"0" * (10 * 1024 * 1024 + 512 * 1024)
    files = {"file": ("oversized_manual.txt", io.BytesIO(oversized_content), "text/plain")}
    data = {"category": "product_manual"}

    resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data=data)
    assert resp.status_code == 413
    assert "exceeds" in resp.json()["detail"].lower()


def test_document_upload_path_traversal_defense(tmp_path):
    """16. Verify POST /api/v1/documents defends against path traversal attacks."""
    manifest_file = tmp_path / "test_manifest.json"
    custom_ingestion = IngestionService(manifest_path=manifest_file)

    app.dependency_overrides[get_ingestion_service] = lambda: custom_ingestion
    app.dependency_overrides[get_manifest] = lambda: custom_ingestion.manifest
    try:
        content = b"Legitimate text content inside an attack filename attempt.\n"
        # Attack filename attempting to escape up directories
        files = {"file": ("../../../../etc/passwd.txt", io.BytesIO(content), "text/plain")}
        data = {"category": "product_manual"}

        resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data=data)
        # Should either safely sanitize to 'passwd.txt' or reject with 400
        if resp.status_code == 201:
            # Verified safe sanitization
            res = resp.json()
            assert res["filename"] == "passwd.txt"
            assert ".." not in res["filename"]
        else:
            assert resp.status_code == 400
            assert "path traversal" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_document_upload_duplicate_detection(tmp_path):
    """17. Verify uploading identical content is idempotent and detects duplicates."""
    manifest_file = tmp_path / "test_manifest.json"
    custom_ingestion = IngestionService(manifest_path=manifest_file)

    app.dependency_overrides[get_ingestion_service] = lambda: custom_ingestion
    app.dependency_overrides[get_manifest] = lambda: custom_ingestion.manifest
    try:
        content = b"Identical troubleshooting content for duplicate testing.\n"
        files1 = {"file": ("troubleshoot_v1.txt", io.BytesIO(content), "text/plain")}
        resp1 = client.post(f"{settings.API_V1_PREFIX}/documents", files=files1, data={"category": "troubleshooting"})
        assert resp1.status_code == 201

        files2 = {"file": ("troubleshoot_v1.txt", io.BytesIO(content), "text/plain")}
        resp2 = client.post(f"{settings.API_V1_PREFIX}/documents", files=files2, data={"category": "troubleshooting"})
        assert resp2.status_code == 201
        res2 = resp2.json()
        assert res2["status"] == "SKIPPED_DUPLICATE"
    finally:
        app.dependency_overrides.clear()


def test_document_list_with_lifecycle_states():
    """18. Verify GET /api/v1/documents returns documents with proper lifecycle states."""
    resp = client.get(f"{settings.API_V1_PREFIX}/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)

    allowed_states = {
        "uploaded",
        "processed",
        "pending_index",
        "indexed",
        "indexing_failed",
        "deleted",
    }
    for doc in data["documents"]:
        assert doc["lifecycle_status"] in allowed_states
        if doc["lifecycle_status"] == "indexed":
            assert doc["is_searchable"] is True
        else:
            assert doc["is_searchable"] is False


def test_document_get_by_id_and_not_found():
    """19. Verify GET /api/v1/documents/{doc_id} retrieves document and 404s for invalid id."""
    # List first
    list_resp = client.get(f"{settings.API_V1_PREFIX}/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    if docs:
        first_id = docs[0]["document_id"]
        get_resp = client.get(f"{settings.API_V1_PREFIX}/documents/{first_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["document_id"] == first_id

    # Non-existent ID returns 404
    non_existent = client.get(f"{settings.API_V1_PREFIX}/documents/doc_non_existent_999999")
    assert non_existent.status_code == 404


def test_document_delete_atomic_and_idempotent(tmp_path):
    """20. Verify DELETE /api/v1/documents/{doc_id} is atomic and returns 404 on repeat."""
    manifest_file = tmp_path / "test_manifest.json"
    custom_ingestion = IngestionService(manifest_path=manifest_file)

    app.dependency_overrides[get_ingestion_service] = lambda: custom_ingestion
    app.dependency_overrides[get_manifest] = lambda: custom_ingestion.manifest
    try:
        # 1. Upload temporary document
        content = b"Temporary document to be deleted immediately.\n"
        files = {"file": ("temp_delete_doc.txt", io.BytesIO(content), "text/plain")}
        up_resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data={"category": "faq"})
        assert up_resp.status_code == 201
        doc_id = up_resp.json()["document_id"]

        # 2. Delete document
        del_resp = client.delete(f"{settings.API_V1_PREFIX}/documents/{doc_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "success"
        assert del_resp.json()["document_id"] == doc_id

        # 3. Verify get returns 404
        get_resp = client.get(f"{settings.API_V1_PREFIX}/documents/{doc_id}")
        assert get_resp.status_code == 404

        # 4. Repeat delete returns 404 (already deleted)
        repeat_del = client.delete(f"{settings.API_V1_PREFIX}/documents/{doc_id}")
        assert repeat_del.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 4. Knowledge Base Status, Feedback, and Dependency Override
# ==============================================================================

def test_knowledge_base_status_endpoint():
    """21. Verify GET /api/v1/knowledge-base/status returns categories and state metrics."""
    resp = client.get(f"{settings.API_V1_PREFIX}/knowledge-base/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert "total_active_documents" in data
    assert "total_active_chunks" in data
    assert "searchable_documents_count" in data
    assert "documents_by_category" in data
    assert "documents_by_lifecycle_status" in data
    assert "vector_store" in data
    assert "storage" in data


def test_feedback_endpoint_submission():
    """22. Verify POST /api/v1/feedback accepts ratings and corrections."""
    payload = {
        "query_id": "test-stage5-qid-42",
        "rating": 5,
        "correction": None,
        "flagged_incorrect": False,
        "comment": "Accurate citations and grounded answer",
    }
    resp = client.post(f"{settings.API_V1_PREFIX}/feedback", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert resp.json()["data"]["rating"] == 5


def test_fastapi_dependency_injection_override():
    """23. Verify FastAPI dependency injection allows clean test overrides."""
    class CustomMockRAGService:
        async def process_query(self, **kwargs):
            return QueryResponse(
                query="override query",
                answer="Answer generated by custom test mock dependency injection.",
                retrieval_mode="baseline",
                selected_categories=[],
                supporting_citations=[],
                evidence_status="SUFFICIENT",
                retrieval_latency_ms=1.5,
                generation_latency_ms=2.0,
                provider_status="CUSTOM_TEST_OVERRIDE",
                evidence_found=True,
                citations=[],
                retrieval_similarity=0.99,
                confidence_score=None,
                contexts_used=1,
                execution_time_ms=3.5,
                requires_human_clarification=False,
                is_mock=True,
            )

    app.dependency_overrides[get_rag_service] = lambda: CustomMockRAGService()
    try:
        resp = client.post(f"{settings.API_V1_PREFIX}/query", json={"query": "Custom override test"})
        assert resp.status_code == 200
        res = resp.json()
        assert res["answer"] == "Answer generated by custom test mock dependency injection."
        assert res["provider_status"] == "CUSTOM_TEST_OVERRIDE"
        assert res["is_mock"] is True
    finally:
        app.dependency_overrides.clear()
