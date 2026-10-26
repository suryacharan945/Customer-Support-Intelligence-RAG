"""Test suite for ChromaSnapshotManager: atomic snapshots, checksums, and verified restoration."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from app.retrieval.chroma_backup import ChromaSnapshotManager, ChromaBackupError


@pytest.fixture
def dummy_chroma_dir():
    """Create a temporary directory structured like a real ChromaDB persistence folder."""
    with tempfile.TemporaryDirectory() as td:
        base_dir = Path(td) / "chroma_source"
        base_dir.mkdir()

        # 1. Create a valid SQLite database with embeddings and collections tables
        sqlite_file = base_dir / "chroma.sqlite3"
        conn = sqlite3.connect(str(sqlite_file))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT);")
        cursor.execute("CREATE TABLE embeddings (id TEXT PRIMARY KEY, collection_id TEXT, document TEXT);")
        cursor.execute("INSERT INTO collections VALUES ('coll_1', 'apexprint_kb');")
        for i in range(21):
            cursor.execute(
                "INSERT INTO embeddings VALUES (?, 'coll_1', ?);",
                (f"chunk_{i:04d}", f"Text content for chunk {i}"),
            )
        conn.commit()
        conn.close()

        # 2. Create dummy HNSW index segment binary directory
        segment_dir = base_dir / "segment_index_hnsw_01"
        segment_dir.mkdir()
        (segment_dir / "index_metadata.bin").write_bytes(b"\x00\x01\x02\x03\x04" * 100)
        (segment_dir / "data_level0.bin").write_bytes(b"\xAA\xBB\xCC\xDD" * 200)

        yield base_dir


def test_chroma_snapshot_creation_and_restoration(dummy_chroma_dir):
    """Test full backup lifecycle: quiescing, zip packaging, manifest generation, and restore."""
    with tempfile.TemporaryDirectory() as td:
        backup_dir = Path(td) / "backups"
        restore_dir = Path(td) / "restored"

        manager = ChromaSnapshotManager(
            source_dir=dummy_chroma_dir,
            backup_destination_dir=backup_dir,
        )

        manifest = manager.create_snapshot(
            collection_name="apexprint_kb",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            distance_metric="cosine",
            chunk_count=21,
            document_ids=["doc_1", "doc_2"],
        )

        # 1. Verify manifest
        assert manifest["collection_name"] == "apexprint_kb"
        assert manifest["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert manifest["embedding_dimension"] == 384
        assert manifest["chunk_count"] == 21
        assert "archive_filename" in manifest
        assert "archive_sha256" in manifest

        archive_path = backup_dir / manifest["archive_filename"]
        assert archive_path.exists()
        assert archive_path.stat().st_size > 0

        # Check latest symlink/copy files
        latest_zip = backup_dir / "chroma_full_snapshot_latest.zip"
        latest_manifest = backup_dir / "chroma_manifest_latest.json"
        assert latest_zip.exists()
        assert latest_manifest.exists()

        # 2. Test verified restore
        restore_result = manager.restore_snapshot(
            snapshot_zip_path=archive_path,
            target_directory=restore_dir,
            expected_sha256=manifest["archive_sha256"],
        )

        assert restore_result["status"] == "RESTORED_OK"
        assert restore_result["sqlite_integrity"] == "ok"
        assert restore_result["chunk_count"] == 21
        assert restore_result["table_count"] >= 2

        # 3. Verify restored HNSW binary artifacts
        restored_bin = restore_dir / "segment_index_hnsw_01" / "index_metadata.bin"
        assert restored_bin.exists()
        assert restored_bin.stat().st_size == 500


def test_restore_fails_on_corrupted_checksum(dummy_chroma_dir):
    """Test that restore_snapshot raises ChromaBackupError when checksum mismatch occurs."""
    with tempfile.TemporaryDirectory() as td:
        backup_dir = Path(td) / "backups"
        restore_dir = Path(td) / "restored"

        manager = ChromaSnapshotManager(
            source_dir=dummy_chroma_dir,
            backup_destination_dir=backup_dir,
        )

        manifest = manager.create_snapshot()
        archive_path = backup_dir / manifest["archive_filename"]

        with pytest.raises(ChromaBackupError) as exc_info:
            manager.restore_snapshot(
                snapshot_zip_path=archive_path,
                target_directory=restore_dir,
                expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )
        assert "checksum mismatch" in str(exc_info.value).lower()
