"""Package Stage 8 Phase 4.7 Release Candidate Standalone Archive."""

import os
import zipfile
from pathlib import Path

def create_archive():
    source_root = Path(".").resolve()
    target_zip = Path(r"G:\My Drive\Internship_RAG_MCP_Capstone\Stage8_Phase4_7_Release_Candidate.zip")
    
    # Exclude patterns
    exclude_dirs = {
        ".git", "node_modules", "venv", ".venv", "__pycache__", ".pytest_cache",
        "tmp", ".chroma_live"
    }
    exclude_extensions = {".pyc", ".pyo", ".pyd"}

    print(f"Creating standalone archive at: {target_zip}")
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        file_count = 0
        total_uncompressed = 0
        for root, dirs, files in os.walk(source_root):
            # Modify dirs in-place to avoid traversing excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_extensions:
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(source_root)
                zf.write(file_path, arcname)
                file_count += 1
                total_uncompressed += file_path.stat().st_size

    archive_size = target_zip.stat().st_size
    print(f"[SUCCESS] Standalone Archive Created:")
    print(f"  Archive Path:       {target_zip}")
    print(f"  Files Archived:     {file_count}")
    print(f"  Uncompressed Size:  {total_uncompressed / (1024 * 1024):.2f} MB")
    print(f"  Compressed Size:    {archive_size / (1024 * 1024):.2f} MB ({archive_size:,} bytes)")

if __name__ == "__main__":
    create_archive()
