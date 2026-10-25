"""
Automated Snapshot & Backup Utility for Internship RAG MCP Capstone.
Safely exports consistent snapshots of source code, vector database, and documentation
to Google Drive without file-lock collisions.

Features:
- Dynamic Google Drive mount detection
- Native SQLite Online Backup API for ChromaDB (properly flushes WAL/SHM into a clean DB)
- Backup retention / rotation policy (max 5 snapshots) to prevent unbounded accumulation
- Cloud synchronization and readability verification
- Automated restoration and integrity verification test
"""

import datetime
import os
import shutil
import sqlite3
import string
import sys
import tempfile
import zipfile
from pathlib import Path

MAX_BACKUP_RETENTION = 5


def find_google_drive() -> Path:
    """Dynamically detect Google Drive virtual mount point (e.g. G:\\, H:\\)."""
    available_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    for drive in available_drives:
        my_drive = Path(drive) / "My Drive"
        if my_drive.is_dir():
            return my_drive

    user_home_gdrive = Path.home() / "Google Drive"
    if user_home_gdrive.is_dir():
        return user_home_gdrive

    return None


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".chroma_live",
    "tmp",
    "temp",
    "node_modules",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp",
}


def rotate_backups(backup_dir: Path, pattern: str, max_count: int = MAX_BACKUP_RETENTION):
    """Keep only the latest `max_count` backups, pruning older files."""
    if not backup_dir.exists():
        return
    files = sorted(backup_dir.glob(pattern), key=lambda f: f.stat().st_mtime)
    while len(files) > max_count:
        oldest = files.pop(0)
        try:
            oldest.unlink()
            print(f"[PRUNE] Rotated out old backup: {oldest.name}")
        except Exception as e:
            print(f"[WARNING] Failed to rotate {oldest.name}: {e}")


def verify_cloud_file(file_path: Path, expected_size: int) -> bool:
    """Verify that a written file exists on the cloud mount, matches size, and is readable."""
    if not file_path.exists():
        print(f"[ERROR] Sync verification failed: {file_path} does not exist.")
        return False
    actual_size = file_path.stat().st_size
    if actual_size != expected_size:
        print(f"[ERROR] Sync verification size mismatch: expected {expected_size}, got {actual_size}.")
        return False
    try:
        with open(file_path, "rb") as f:
            _ = f.read(min(actual_size, 4096))
        return True
    except Exception as e:
        print(f"[ERROR] Sync verification read error: {e}")
        return False


def backup_source_code(local_root: Path, drive_project_root: Path, timestamp: str) -> Path:
    """Create a clean snapshot zip of the source code and save to Google Drive."""
    dest_source_dir = drive_project_root / "01_Source_Code"
    dest_backups_dir = drive_project_root / "11_Backups"
    dest_source_dir.mkdir(parents=True, exist_ok=True)
    dest_backups_dir.mkdir(parents=True, exist_ok=True)

    zip_filename = f"source_backup_{timestamp}.zip"
    dest_zip_path = dest_backups_dir / zip_filename

    # Build zip locally in temporary directory to ensure atomic write and exact size
    with tempfile.TemporaryDirectory(prefix="src_backup_build_") as tmp_dir:
        local_tmp_zip = Path(tmp_dir) / zip_filename
        print(f"[BACKUP] Packaging source code into {zip_filename}...")
        with zipfile.ZipFile(local_tmp_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(local_root):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in EXCLUDE_EXTENSIONS or file.startswith(".env"):
                        continue

                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(local_root)
                    zip_file.write(full_path, arcname=str(rel_path))

        expected_size = local_tmp_zip.stat().st_size
        shutil.copy2(local_tmp_zip, dest_zip_path)

    if not verify_cloud_file(dest_zip_path, expected_size):
        raise IOError(f"Cloud synchronization verification failed for {dest_zip_path}")

    # Mirror latest copy
    latest_zip = dest_source_dir / "latest_source.zip"
    shutil.copy2(dest_zip_path, latest_zip)

    # Prune old archives
    rotate_backups(dest_backups_dir, "source_backup_*.zip", MAX_BACKUP_RETENTION)

    print(f"[OK] Source backup verified on Google Drive ({expected_size:,} bytes).")
    return dest_zip_path


def backup_chroma_db(local_root: Path, drive_project_root: Path, timestamp: str) -> Path:
    """
    Safely back up ChromaDB database files using SQLite Online Backup API.
    Flushes and merges WAL/SHM transactions into a clean, consistent snapshot.
    """
    local_chroma = local_root / ".chroma_live"
    dest_vector_dir = drive_project_root / "05_Vector_Database_Backups"
    dest_vector_dir.mkdir(parents=True, exist_ok=True)

    if not local_chroma.exists() or not any(local_chroma.iterdir()):
        print("[NOTICE] No active local ChromaDB database found to back up.")
        return None

    dest_zip = dest_vector_dir / f"chroma_snapshot_{timestamp}.zip"
    print(f"[BACKUP] Performing consistent ChromaDB backup to {dest_zip.name}...")

    # Use a temporary directory on local C: drive to construct the consistent quiesced snapshot
    with tempfile.TemporaryDirectory(prefix="chroma_backup_quiesce_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        for root, _, files in os.walk(local_chroma):
            for file in files:
                src_file = Path(root) / file
                rel_file = src_file.relative_to(local_chroma)
                target_file = tmp_path / rel_file
                target_file.parent.mkdir(parents=True, exist_ok=True)

                if file.endswith(".sqlite3"):
                    # Use SQLite Online Backup API to safely capture live WAL state
                    print(f"  -> Quiescing SQLite database via Online Backup API: {file}")
                    src_conn = sqlite3.connect(f"file:{src_file}?mode=ro", uri=True)
                    try:
                        src_conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
                    except Exception:
                        pass
                    dest_conn = sqlite3.connect(str(target_file))
                    try:
                        src_conn.backup(dest_conn)
                    finally:
                        dest_conn.close()
                        src_conn.close()
                elif file.endswith(("-wal", "-shm")):
                    # Skip separate journals because they are now safely merged by sqlite3.backup()
                    continue
                else:
                    # Copy HNSW / Parquet index segments
                    shutil.copy2(src_file, target_file)

        # Package quiesced directory into local zip first for atomic upload
        local_dest_zip = tmp_path / dest_zip.name
        with zipfile.ZipFile(local_dest_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(tmp_path):
                for file in files:
                    if file == dest_zip.name:
                        continue
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(tmp_path)
                    zip_file.write(full_path, arcname=str(rel_path))

        expected_size = local_dest_zip.stat().st_size
        shutil.copy2(local_dest_zip, dest_zip)

    if not verify_cloud_file(dest_zip, expected_size):
        raise IOError(f"Cloud synchronization verification failed for {dest_zip}")

    rotate_backups(dest_vector_dir, "chroma_snapshot_*.zip", MAX_BACKUP_RETENTION)
    print(f"[OK] ChromaDB consistent snapshot verified on Google Drive ({expected_size:,} bytes).")
    return dest_zip


def test_restore_integrity(backup_zip_path: Path) -> bool:
    """
    Verify backup integrity by performing a sandboxed restoration test.
    Checks archive structure and runs PRAGMA integrity_check on all restored SQLite databases.
    """
    if not backup_zip_path or not backup_zip_path.exists():
        return False

    print(f"[TEST] Testing restoration integrity for {backup_zip_path.name}...")
    with tempfile.TemporaryDirectory(prefix="test_restore_sandbox_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        with zipfile.ZipFile(backup_zip_path, "r") as zf:
            zf.extractall(tmp_path)

        sqlite_files = list(tmp_path.glob("**/*.sqlite3"))
        if sqlite_files:
            for db_file in sqlite_files:
                conn = sqlite3.connect(str(db_file))
                try:
                    cur = conn.cursor()
                    cur.execute("PRAGMA integrity_check;")
                    result = cur.fetchone()
                    if result != ("ok",):
                        print(f"[FAIL] SQLite integrity check failed for {db_file.name}: {result}")
                        return False
                    print(f"[PASS] PRAGMA integrity_check passed for {db_file.name}: {result[0]}")
                finally:
                    conn.close()
        else:
            print(f"[PASS] Non-database archive unpacked cleanly ({len(list(tmp_path.glob('**/*')))} entries).")

    return True


def main():
    print("=" * 60)
    print("Cloud Backup & Snapshot Tool")
    print("=" * 60)

    my_drive = find_google_drive()
    if not my_drive:
        print("[ERROR] Google Drive mount not found. Connect Google Drive for Desktop first.")
        sys.exit(1)

    drive_project_root = my_drive / "Internship_RAG_MCP_Capstone"
    if not drive_project_root.exists():
        print(f"[ERROR] Target project root does not exist: {drive_project_root}")
        sys.exit(1)

    local_root = Path(__file__).resolve().parent.parent
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    src_zip = backup_source_code(local_root, drive_project_root, timestamp)
    test_restore_integrity(src_zip)

    chroma_zip = backup_chroma_db(local_root, drive_project_root, timestamp)
    if chroma_zip:
        test_restore_integrity(chroma_zip)

    print("=" * 60)
    print("[ALL DONE] Project state safely synchronized to Google Drive.")
    print("=" * 60)


if __name__ == "__main__":
    main()
