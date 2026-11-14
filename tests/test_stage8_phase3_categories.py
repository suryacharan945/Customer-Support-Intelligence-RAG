"""Stage 8 Phase 3.1 Regression Tests: Category Compatibility.

Verifies end-to-end category acceptance and persistence across all 8 supported categories:
- general
- engineering
- architecture
- evaluation
- product_manual
- troubleshooting
- warranty
- faq
"""

import io
import tempfile
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.api.deps import get_ingestion_service, get_manifest
from app.services.ingestion_service import IngestionService
from app.ingestion.loader import (
    VALID_CATEGORIES,
    DocumentLoader,
    InvalidCategoryError,
)

ALL_EIGHT_CATEGORIES = [
    "general",
    "engineering",
    "architecture",
    "evaluation",
    "product_manual",
    "troubleshooting",
    "warranty",
    "faq",
]

client = TestClient(app)


def test_loader_valid_categories_set():
    """Verify VALID_CATEGORIES contains all 8 required categories."""
    for cat in ALL_EIGHT_CATEGORIES:
        assert cat in VALID_CATEGORIES, f"Category '{cat}' missing from VALID_CATEGORIES"


@pytest.mark.parametrize("category", ALL_EIGHT_CATEGORIES)
def test_loader_accepts_all_eight_categories(tmp_path, category):
    """Verify DocumentLoader accepts and normalizes each of the 8 categories."""
    loader = DocumentLoader()
    doc_file = tmp_path / f"test_{category}.md"
    doc_file.write_text(f"# Test {category}\n\nContent for {category} category.\n")

    doc = loader.load_file(doc_file, category=category)
    assert doc.category == category


def test_loader_rejects_invalid_category(tmp_path):
    """Verify DocumentLoader rejects arbitrary invalid categories with InvalidCategoryError."""
    loader = DocumentLoader()
    doc_file = tmp_path / "test_invalid.md"
    doc_file.write_text("# Invalid\n\nContent.\n")

    with pytest.raises(InvalidCategoryError) as exc_info:
        loader.load_file(doc_file, category="unsupported_random_category_xyz")
    assert "Invalid category" in str(exc_info.value)


@pytest.mark.parametrize("category", ALL_EIGHT_CATEGORIES)
def test_api_upload_persists_category_metadata(tmp_path, category):
    """Verify POST /api/v1/documents accepts and correctly persists all 8 categories."""
    manifest_file = tmp_path / f"manifest_{category}.json"
    custom_ingestion = IngestionService(manifest_path=manifest_file)

    app.dependency_overrides[get_ingestion_service] = lambda: custom_ingestion
    app.dependency_overrides[get_manifest] = lambda: custom_ingestion.manifest
    try:
        content = f"# Test Document\n\nTesting persistence for category '{category}'.\n".encode("utf-8")
        files = {"file": (f"test_doc_{category}.md", io.BytesIO(content), "text/markdown")}
        data = {"category": category}

        resp = client.post(f"{settings.API_V1_PREFIX}/documents", files=files, data=data)
        assert resp.status_code == 201
        res = resp.json()
        assert res["status"] == "SUCCESS"
        assert res["category"] == category, f"Expected category '{category}', got '{res['category']}'"
    finally:
        app.dependency_overrides.clear()
