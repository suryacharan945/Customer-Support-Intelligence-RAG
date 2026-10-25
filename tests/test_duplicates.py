"""Test suite for duplicate detection, versioning, manifest persistence, and failure isolation."""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app.ingestion.loader import DocumentLoader, CorruptedFileError
from app.ingestion.manifest import IngestionManifest
from app.services.ingestion_service import IngestionService


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td)
        manifest_file = workspace / "manifest.json"
        service = IngestionService(manifest_path=manifest_file)
        yield workspace, manifest_file, service


def test_duplicate_ingestion_skipped(temp_workspace):
    """17. Test that re-ingesting identical file skips duplicate processing."""
    workspace, manifest_file, service = temp_workspace
    doc_path = workspace / "warranty_terms.md"
    doc_path.write_text("Standard 12-month limited warranty text for ApexPrint.", encoding="utf-8")

    # First ingestion
    res1 = service.ingest_file(doc_path, category="warranty")
    assert res1["status"] == "SUCCESS"
    assert res1["chunk_count"] > 0
    assert len(res1["chunks"]) > 0

    # Second ingestion of identical content
    res2 = service.ingest_file(doc_path, category="warranty")
    assert res2["status"] == "SKIPPED_DUPLICATE"
    assert res2["chunks"] == []
    assert res2["document_id"] == res1["document_id"]
    assert res2["record"]["version"] == 1


def test_changed_document_content_creates_new_version(temp_workspace):
    """18. Test that modifying file content increments version and updates manifest."""
    workspace, manifest_file, service = temp_workspace
    doc_path = workspace / "troubleshooting.txt"
    doc_path.write_text("Initial troubleshooting revision 1.", encoding="utf-8")

    res1 = service.ingest_file(doc_path, category="troubleshooting")
    assert res1["status"] == "SUCCESS"
    assert res1["record"]["version"] == 1
    doc_id_v1 = res1["document_id"]

    # Modify content of same filename
    doc_path.write_text("Updated troubleshooting revision 2 with new Wi-Fi instructions.", encoding="utf-8")

    res2 = service.ingest_file(doc_path, category="troubleshooting")
    assert res2["status"] == "UPDATED"
    assert res2["record"]["version"] == 2
    assert res2["document_id"] != doc_id_v1  # Deterministic hash ID changed
    assert len(res2["chunks"]) > 0


def test_persistent_manifest_across_restarts(temp_workspace):
    """19. Test that manifest state persists across process restart / new instance."""
    workspace, manifest_file, service1 = temp_workspace
    doc_path = workspace / "faq.md"
    doc_path.write_text("Frequently asked questions about ApexPrint cartridges.", encoding="utf-8")

    res1 = service1.ingest_file(doc_path, category="faq")
    assert res1["status"] == "SUCCESS"

    # Simulate restart by instantiating a completely new IngestionService reading manifest_file
    service2 = IngestionService(manifest_path=manifest_file)
    eval_status, existing = service2.manifest.evaluate_file("faq", "faq.md", res1["record"]["content_hash"])
    assert eval_status == "UNCHANGED"
    assert existing["document_id"] == res1["document_id"]
    assert existing["version"] == 1

    # Ingesting with the restarted service should skip re-chunking
    res2 = service2.ingest_file(doc_path, category="faq")
    assert res2["status"] == "SKIPPED_DUPLICATE"


def test_safe_failure_without_modifying_manifest(temp_workspace):
    """20. Test that an ingestion failure does not corrupt or modify the manifest."""
    workspace, manifest_file, service = temp_workspace

    # Ingest a valid document first
    valid_file = workspace / "valid.txt"
    valid_file.write_text("Valid text content.", encoding="utf-8")
    service.ingest_file(valid_file, category="product_manual")

    manifest_before = manifest_file.read_text(encoding="utf-8")

    # Attempt to ingest a corrupted file
    bad_pdf = workspace / "bad.pdf"
    bad_pdf.write_bytes(b"%PDF-INVALID-DATA")

    with pytest.raises(CorruptedFileError):
        service.ingest_file(bad_pdf, category="product_manual")

    manifest_after = manifest_file.read_text(encoding="utf-8")
    assert json.loads(manifest_before)["documents"] == json.loads(manifest_after)["documents"]
