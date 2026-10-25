"""
Automated Snapshot & Backup Utility for Internship RAG MCP Capstone.
Safely exports consistent snapshots of source code, vector database, and documentation
to Google Drive without file-lock collisions.
"""

import datetime
import os
import shutil
import string
import sys
import zipfile
from pathlib import Path


def find_google_drive():
    """Detect the Google Drive mount point (e.g. G:, H:, etc.)."""
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
    ".sqlite3-wal",
    ".sqlite3-shm",
}


def backup_source_code(local_root: Path, drive_project_root: Path, timestamp: str):
    """Create a clean snapshot zip of the source code and save to Google Drive."""
    dest_source_dir = drive_project_root / "01_Source_Code"
    dest_backups_dir = drive_project_root / "11_Backups"
    
    zip_filename = f"source_backup_{timestamp}.zip"
    zip_path = dest_backups_dir / zip_filename

    print(f"[BACKUP] Packaging source code into {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(local_root):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in EXCLUDE_EXTENSIONS:
                    continue
                if file.startswith(".env"):
                    continue

                full_path = Path(root) / file
                rel_path = full_path.relative_to(local_root)
                zip_file.write(full_path, arcname=str(rel_path))

    # Also keep latest copy unzipped in 01_Source_Code for easy reference
    latest_zip = dest_source_dir / "latest_source.zip"
    shutil.copy2(zip_path, latest_zip)
    print(f"[OK] Source backup complete ({zip_path.stat().st_size:,} bytes).")


def backup_chroma_db(local_root: Path, drive_project_root: Path, timestamp: str):
    """Safely back up ChromaDB database files if present."""
    local_chroma = local_root / ".chroma_live"
    dest_vector_dir = drive_project_root / "05_Vector_Database_Backups"
    
    if not local_chroma.exists() or not any(local_chroma.iterdir()):
        print("[NOTICE] No active local ChromaDB database found to back up.")
        return

    dest_zip = dest_vector_dir / f"chroma_snapshot_{timestamp}.zip"
    print(f"[BACKUP] Backing up ChromaDB snapshot to {dest_zip.name}...")
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(local_chroma):
            for file in files:
                if file.endswith("-wal") or file.endswith("-shm"):
                    continue  # exclude active transaction journals
                full_path = Path(root) / file
                rel_path = full_path.relative_to(local_chroma)
                zip_file.write(full_path, arcname=str(rel_path))

    print(f"[OK] ChromaDB snapshot backed up successfully ({dest_zip.stat().st_size:,} bytes).")


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

    backup_source_code(local_root, drive_project_root, timestamp)
    backup_chroma_db(local_root, drive_project_root, timestamp)

    print("=" * 60)
    print("[ALL DONE] Project state safely synchronized to Google Drive.")
    print("=" * 60)


if __name__ == "__main__":
    main()
