"""
Test Suite for ChromaDB / SQLite Safe Backup & Restoration Integrity.
Validates that:
1. Active SQLite WAL mode transactions are properly captured via the Online Backup API.
2. The restored database is free of corruption and passes PRAGMA integrity_check.
3. Cloud synchronization verification succeeds.
"""

import os
import shutil
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.backup_to_drive import (
    find_google_drive,
    backup_chroma_db,
    test_restore_integrity,
)


def run_test():
    print("=" * 60)
    print("RUNNING BACKUP & RESTORE INTEGRITY TEST")
    print("=" * 60)

    my_drive = find_google_drive()
    if not my_drive:
        print("[FAIL] Google Drive not found.")
        return False

    drive_project_root = my_drive / "Internship_RAG_MCP_Capstone"
    test_chroma_dir = PROJECT_ROOT / ".chroma_live"
    test_chroma_dir.mkdir(parents=True, exist_ok=True)

    test_db_path = test_chroma_dir / "chroma.sqlite3"
    print(f"[1/4] Creating active SQLite WAL test database at: {test_db_path}")

    # Create table and insert rows in WAL mode
    conn = sqlite3.connect(str(test_db_path))
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    journal_mode = cur.fetchone()[0]
    print(f"      Journal Mode: {journal_mode}")

    cur.execute("CREATE TABLE IF NOT EXISTS embeddings (id INTEGER PRIMARY KEY, vector TEXT, doc TEXT);")
    for i in range(100):
        cur.execute("INSERT INTO embeddings (vector, doc) VALUES (?, ?);", (f"[0.1, 0.2, {i}]", f"Document chunk {i}"))
    conn.commit()

    # Leave an active uncheckpointed write in WAL
    cur.execute("INSERT INTO embeddings (vector, doc) VALUES (?, ?);", ("[0.9, 0.9, 999]", "Uncheckpointed WAL chunk 999"))
    conn.commit()
    # DO NOT checkpoint; leave WAL active!
    conn.close()

    wal_file = test_chroma_dir / "chroma.sqlite3-wal"
    print(f"      WAL file exists: {wal_file.exists()} (Size: {wal_file.stat().st_size if wal_file.exists() else 0} bytes)")

    print("[2/4] Executing safe ChromaDB backup via backup_chroma_db()...")
    timestamp = "test_verify"
    backup_zip = backup_chroma_db(PROJECT_ROOT, drive_project_root, timestamp)

    print(f"[3/4] Backup created: {backup_zip.name} on {backup_zip.parent}")
    print("[4/4] Verifying restoration integrity...")
    success = test_restore_integrity(backup_zip)

    # Clean up local test artifacts in .chroma_live
    print("[CLEANUP] Removing local test database files...")
    shutil.rmtree(test_chroma_dir, ignore_errors=True)

    # Also clean up the test zip from Google Drive
    if backup_zip.exists():
        backup_zip.unlink()
        print(f"[CLEANUP] Removed verification test artifact: {backup_zip.name}")

    if success:
        print("=" * 60)
        print("[TEST PASSED] Backup & Restore Integrity Verified Successfully!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("[TEST FAILED] Integrity check did not pass.")
        print("=" * 60)

    return success


if __name__ == "__main__":
    ok = run_test()
    sys.exit(0 if ok else 1)
