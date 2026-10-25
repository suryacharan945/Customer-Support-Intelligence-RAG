"""Unit tests for system health diagnostic and root endpoints."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Verify that the root endpoint returns 200 and valid links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["docs"] == "/docs"
    assert data["health"] == f"{settings.API_V1_PREFIX}/health"


def test_health_check_endpoint():
    """Verify system health diagnostics reporting."""
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.PROJECT_NAME
    assert "storage" in data
    assert "compute" in data
    assert data["storage"]["google_drive_root"] == settings.GOOGLE_DRIVE_ROOT


def test_rag_mock_query():
    """Verify that the RAG endpoint processes queries with mock client without errors."""
    payload = {
        "query": "How do I reset my printer?",
        "session_id": "test-session-123",
        "top_k": 3,
    }
    response = client.post(f"{settings.API_V1_PREFIX}/rag/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["confidence_score"] > 0.0
    assert len(data["citations"]) > 0


def test_feedback_submission():
    """Verify recording feedback in the feedback endpoint."""
    payload = {
        "query_id": "qid-001",
        "rating": 5,
        "correction": None,
        "flagged_incorrect": False,
        "comment": "Very accurate instructions",
    }
    response = client.post(f"{settings.API_V1_PREFIX}/feedback/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
