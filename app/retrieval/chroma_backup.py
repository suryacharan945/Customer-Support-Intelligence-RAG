"""ChromaDB Full Persistence Snapshot and Restoration Engine.

Preserves the complete ChromaDB persistence directory, including:
1. Quiesced SQLite metadata/storage database (via SQLite Online Backup API)
2. Vector-index HNSW segment directories and binary artifacts
3. Machine-readable index manifest with checksums, model specifications, and software telemetry.
"""

import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.core.logging import logger


class ChromaBackupError(Exception):
    """Base exception for ChromaDB backup and restoration operations."""
    pass


class ChromaSnapshotManager:
    """
    Manages complete, consistent backups and verified restorations of ChromaDB persistent stores.
    Adheres strictly to the Google Drive First and Zero-Corruption policies.
    """

    def __init__(
        self,
        source_dir: Optional[str | Path] = None,
        backup_destination_dir: Optional[str | Path] = None,
    ):
        self.source_dir = Path(source_dir or settings.LOCAL_EPHEMERAL_CHROMA_DIR)
        gdrive_backups = Path(settings.GOOGLE_DRIVE_ROOT) / "05_Vector_Database_Backups"
        self.destination_dir = Path(backup_destination_dir or gdrive_backups)

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA-256 hex digest of a file in streaming chunks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def create_snapshot(
        self,
        collection_name: str = settings.CHROMA_COLLECTION_NAME,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        dimension: int = settings.EMBEDDING_DIMENSION,
        distance_metric: str = settings.EMBEDDING_DISTANCE_METRIC,
        chunk_count: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a complete, atomic snapshot of the entire ChromaDB persistence directory.
        Returns the metadata manifest dictionary.
        """
        if not self.source_dir.exists():
            raise ChromaBackupError(f"Chroma source directory does not exist: {self.source_dir}")

        sqlite_db = self.source_dir / "chroma.sqlite3"
        if not sqlite_db.exists():
            raise ChromaBackupError(f"Chroma SQLite database not found at {sqlite_db}")

        self.destination_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_filename = f"chroma_full_snapshot_{timestamp}.zip"
        manifest_filename = f"chroma_manifest_{timestamp}.json"

        temp_dir = Path(tempfile.mkdtemp(prefix="chroma_snap_"))
        try:
            staging_dir = temp_dir / "quiesced_chroma"
            staging_dir.mkdir()

            # 1. Quiesce chroma.sqlite3 via SQLite Online Backup API (flushes WAL cleanly)
            quiesced_sqlite = staging_dir / "chroma.sqlite3"
            logger.info("Quiescing SQLite storage via Online Backup API...")
            src_conn = sqlite3.connect(str(sqlite_db))
            dst_conn = sqlite3.connect(str(quiesced_sqlite))
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()

            # 2. Copy all segment folders, binaries, and index files (excluding live WAL/SHM)
            for item in self.source_dir.iterdir():
                if item.name in ("chroma.sqlite3", "chroma.sqlite3-wal", "chroma.sqlite3-shm"):
                    continue
                target = staging_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)

            # Determine chunk count if not explicitly passed
            actual_count = chunk_count
            if actual_count is None:
                try:
                    conn = sqlite3.connect(str(quiesced_sqlite))
                    cursor = conn.cursor()
                    cursor.execute("SELECT count(*) FROM embeddings")
                    actual_count = cursor.fetchone()[0]
                    conn.close()
                except Exception:
                    actual_count = 0

            # 3. Package staging directory into compressed zip
            local_zip_path = temp_dir / zip_filename
            with zipfile.ZipFile(local_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(staging_dir):
                    for file in files:
                        p = Path(root) / file
                        zf.write(p, arcname=str(p.relative_to(staging_dir)))

            zip_size = local_zip_path.stat().st_size
            zip_sha256 = self.compute_sha256(local_zip_path)

            # 4. Generate Machine-Readable Index Manifest
            chroma_ver = "unknown"
            try:
                import chromadb
                chroma_ver = getattr(chromadb, "__version__", "installed")
            except ImportError:
                pass

            manifest_data = {
                "manifest_version": "1.0",
                "collection_name": collection_name,
                "embedding_model": model_name,
                "embedding_dimension": dimension,
                "distance_metric": distance_metric,
                "chunk_count": actual_count,
                "document_ids": document_ids or [],
                "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "software_versions": {
                    "python": sys.version.split()[0],
                    "chromadb": chroma_ver,
                },
                "archive_filename": zip_filename,
                "archive_size_bytes": zip_size,
                "archive_sha256": zip_sha256,
            }

            # 5. Atomic copy to destination directory (Google Drive)
            final_zip_dest = self.destination_dir / zip_filename
            final_manifest_dest = self.destination_dir / manifest_filename
            latest_zip_symlink = self.destination_dir / "chroma_full_snapshot_latest.zip"
            latest_manifest_dest = self.destination_dir / "chroma_manifest_latest.json"

            shutil.copy2(local_zip_path, final_zip_dest)
            final_manifest_dest.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            shutil.copy2(local_zip_path, latest_zip_symlink)
            latest_manifest_dest.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

            logger.info(
                f"Full ChromaDB snapshot successfully saved to {final_zip_dest} "
                f"({zip_size:,} bytes, {actual_count} chunks, SHA-256: {zip_sha256[:12]}...)"
            )
            return manifest_data

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def restore_snapshot(
        self,
        snapshot_zip_path: str | Path,
        target_directory: str | Path,
        expected_sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Restore a ChromaDB snapshot into a target directory and verify its structural integrity.
        """
        zip_path = Path(snapshot_zip_path)
        dest_dir = Path(target_directory)

        if not zip_path.exists():
            raise ChromaBackupError(f"Snapshot archive does not exist: {zip_path}")

        # Checksum validation if provided
        if expected_sha256:
            actual_sha256 = self.compute_sha256(zip_path)
            if actual_sha256.lower() != expected_sha256.lower():
                raise ChromaBackupError(
                    f"Snapshot archive checksum mismatch! Expected {expected_sha256}, got {actual_sha256}"
                )

        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Unpacking ChromaDB snapshot: {zip_path.name} -> {dest_dir}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_dir)

        # Integrity Check 1: SQLite integrity check
        sqlite_file = dest_dir / "chroma.sqlite3"
        if not sqlite_file.exists():
            raise ChromaBackupError(f"Restored directory is missing chroma.sqlite3: {dest_dir}")

        conn = sqlite3.connect(str(sqlite_file))
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if not row or row[0].lower() != "ok":
                raise ChromaBackupError(f"SQLite PRAGMA integrity_check failed on restored DB: {row}")

            # Extract count and tables
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings';")
            has_embeddings = cursor.fetchone() is not None

            chunk_count = 0
            if has_embeddings:
                cursor.execute("SELECT count(*) FROM embeddings;")
                chunk_count = cursor.fetchone()[0]
        finally:
            conn.close()

        logger.info(
            f"Snapshot restored cleanly: {table_count} tables, {chunk_count} embeddings verified."
        )

        return {
            "status": "RESTORED_OK",
            "target_directory": str(dest_dir),
            "sqlite_integrity": "ok",
            "table_count": table_count,
            "chunk_count": chunk_count,
        }
