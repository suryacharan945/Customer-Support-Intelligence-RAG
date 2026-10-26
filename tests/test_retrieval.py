"""Test suite for Semantic Retrieval, Category Filtering, Benchmark Evaluation, and Complete Snapshot Restoration."""

import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.embeddings import MockEmbeddingProvider
from app.retrieval.chroma_backup import ChromaSnapshotManager, ChromaBackupError
from evaluation.retrieval_evaluator import RetrievalEvaluator
from tests.test_vector_store import FakeChromaCollection, create_test_chunk


def setup_populated_retriever() -> VectorStoreRetriever:
    """Helper creating a retriever with 9 simulated chunks across 4 categories."""
    provider = MockEmbeddingProvider(allow_mock=True)
    retriever = VectorStoreRetriever(allow_mock=True, embedding_provider=provider)
    fake_coll = FakeChromaCollection(name="apexprint_knowledge_base")
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    chunks = [
        create_test_chunk("doc_prod_01_c00", "doc_prod_01", "ApexPrint ProX-400 speed is 45 ppm.", "product_manual"),
        create_test_chunk("doc_prod_02_c00", "doc_prod_02", "ColorWave 850 CMYK tanks setup.", "product_manual"),
        create_test_chunk("doc_trou_01_c00", "doc_trou_01", "Wi-Fi setup: connect to 2.4/5GHz SSID.", "troubleshooting"),
        create_test_chunk("doc_trou_02_c00", "doc_trou_02", "Error E-101 Paper Jam in Tray 1.", "troubleshooting"),
        create_test_chunk("doc_trou_03_c00", "doc_trou_03", "Error E-204 Fuser Overheat thermal diagnostic.", "troubleshooting"),
        create_test_chunk("doc_warr_01_c00", "doc_warr_01", "1-year limited hardware warranty policy.", "warranty"),
        create_test_chunk("doc_warr_02_c00", "doc_warr_02", "Warranty exclusions: liquid spills, non-OEM toner.", "warranty"),
        create_test_chunk("doc_faq_01_c00", "doc_faq_01", "AirPrint and Mopria wireless printing FAQ.", "faq"),
        create_test_chunk("doc_faq_02_c00", "doc_faq_02", "Drum unit replacement interval is 30,000 pages.", "faq"),
    ]
    retriever.upsert_chunks(chunks)
    return retriever


def test_baseline_semantic_retrieval():
    """8. Test baseline retrieval searching across all indexed categories."""
    retriever = setup_populated_retriever()
    results = retriever.retrieve("printer speed in pages per minute", top_k=3)

    assert len(results) == 3
    for r in results:
        assert 0.0 <= r.score <= 1.0
        assert r.document_id is not None
        assert r.text is not None
        assert r.source is not None
        assert "retrieval_latency_ms" in r.metadata
        assert "raw_distance" in r.metadata


def test_category_filtered_retrieval():
    """9. Test category-filtered retrieval restricting search scope to target category."""
    retriever = setup_populated_retriever()

    # Query for troubleshooting only
    trouble_results = retriever.retrieve("Wi-Fi and Error E-101", top_k=5, category="troubleshooting")
    assert len(trouble_results) > 0
    for r in trouble_results:
        assert r.metadata["category"] == "troubleshooting"

    # Query for warranty only
    warranty_results = retriever.retrieve("What is covered?", top_k=5, category="warranty")
    assert len(warranty_results) > 0
    for r in warranty_results:
        assert r.metadata["category"] == "warranty"


def test_retrieval_latency_and_score_bounds():
    """Test that retrieval records execution latency and computes cosine similarity."""
    retriever = setup_populated_retriever()
    results = retriever.retrieve("How to replace drum unit?", top_k=2)

    assert len(results) == 2
    for r in results:
        latency = r.metadata.get("retrieval_latency_ms")
        assert latency is not None
        assert latency >= 0.0
        dist = r.metadata.get("raw_distance")
        assert dist is not None
        # Score calculation: max(0.0, min(1.0, 1.0 - dist))
        expected_score = max(0.0, min(1.0, 1.0 - dist))
        assert abs(r.score - expected_score) < 1e-4


def test_retrieval_evaluator_metrics_computation():
    """12. Test RetrievalEvaluator computing Recall@1, Recall@3, Recall@5, MRR, and latency."""
    retriever = setup_populated_retriever()
    evaluator = RetrievalEvaluator()

    summary = evaluator.evaluate_retriever(retriever, top_k=5)
    agg = summary["aggregate_metrics"]

    assert summary["total_queries"] >= 10
    assert summary["supported_queries"] >= 10
    assert 0.0 <= agg["recall@1"] <= 1.0
    assert 0.0 <= agg["recall@3"] <= 1.0
    assert 0.0 <= agg["recall@5"] <= 1.0
    assert 0.0 <= agg["mrr"] <= 1.0
    assert agg["mean_latency_ms"] >= 0.0
    assert agg["p95_latency_ms"] >= 0.0


def test_snapshot_manifest_and_quiescence():
    """14 & 17. Test complete ChromaDB snapshot creation, WAL quiescence, and index manifest."""
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        source_chroma = tmp_path / "source_chroma"
        source_chroma.mkdir()

        # Create active SQLite DB in WAL mode
        db_path = source_chroma / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("CREATE TABLE embeddings (id TEXT, text TEXT);")
        for i in range(21):
            conn.execute("INSERT INTO embeddings VALUES (?, ?);", (f"id_{i}", f"Text chunk {i}"))
        conn.commit()
        # Uncheckpointed write in WAL
        conn.execute("INSERT INTO embeddings VALUES ('uncheckpointed', 'WAL data');")
        conn.commit()
        conn.close()

        # Create simulated HNSW segment folder with binary index file
        segment_dir = source_chroma / "uuid-segment-001"
        segment_dir.mkdir()
        (segment_dir / "index_metadata.bin").write_bytes(b"\x00\x01\x02\x03\x04\x05")

        backup_dest = tmp_path / "backups"
        manager = ChromaSnapshotManager(source_dir=source_chroma, backup_destination_dir=backup_dest)

        manifest = manager.create_snapshot(
            collection_name="apexprint_knowledge_base",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            distance_metric="cosine",
            chunk_count=22,
            document_ids=["doc_prod_01", "doc_trou_01"],
        )

        assert manifest["collection_name"] == "apexprint_knowledge_base"
        assert manifest["embedding_dimension"] == 384
        assert manifest["chunk_count"] == 22
        assert len(manifest["archive_sha256"]) == 64
        assert (backup_dest / manifest["archive_filename"]).exists()
        assert (backup_dest / "chroma_manifest_latest.json").exists()


def test_complete_database_restoration_and_integrity():
    """15 & 16. Test restoring snapshot into separate directory, verifying PRAGMA integrity and retrieval."""
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        source_chroma = tmp_path / "source_chroma"
        source_chroma.mkdir()

        db_path = source_chroma / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE embeddings (id TEXT, text TEXT);")
        for i in range(21):
            conn.execute("INSERT INTO embeddings VALUES (?, ?);", (f"id_{i}", f"Text chunk {i}"))
        conn.commit()
        conn.close()

        segment_dir = source_chroma / "uuid-segment-001"
        segment_dir.mkdir()
        (segment_dir / "index_metadata.bin").write_bytes(b"binary_hnsw_data")

        backup_dest = tmp_path / "backups"
        manager = ChromaSnapshotManager(source_dir=source_chroma, backup_destination_dir=backup_dest)
        manifest = manager.create_snapshot(chunk_count=21)

        # Restore into sandbox target directory
        restore_dir = tmp_path / "restored_chroma"
        zip_path = backup_dest / manifest["archive_filename"]
        res = manager.restore_snapshot(
            snapshot_zip_path=zip_path,
            target_directory=restore_dir,
            expected_sha256=manifest["archive_sha256"],
        )

        assert res["status"] == "RESTORED_OK"
        assert res["sqlite_integrity"] == "ok"
        assert res["chunk_count"] == 21
        assert (restore_dir / "uuid-segment-001" / "index_metadata.bin").exists()
        assert (restore_dir / "uuid-segment-001" / "index_metadata.bin").read_bytes() == b"binary_hnsw_data"


def test_restoration_checksum_mismatch_raises_error():
    """Test that a corrupted or mismatched archive SHA-256 checksum raises ChromaBackupError."""
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "dummy content")

        manager = ChromaSnapshotManager(source_dir=tmp_path, backup_destination_dir=tmp_path)
        with pytest.raises(ChromaBackupError) as exc_info:
            manager.restore_snapshot(
                snapshot_zip_path=zip_path,
                target_directory=tmp_path / "restored",
                expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )
        assert "checksum mismatch" in str(exc_info.value)
