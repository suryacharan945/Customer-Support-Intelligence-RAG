"""
Storage and Synchronization Management Script for Internship RAG MCP Capstone.
Verifies Google Drive mount, creates the folder hierarchy, and handles safe backups.
"""

import os
import shutil
import string
import sys
from pathlib import Path


def find_google_drive():
    """Detect the Google Drive mount point (e.g. G:, H:, etc.)."""
    # Check common drive letters
    available_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    for drive in available_drives:
        my_drive = Path(drive) / "My Drive"
        if my_drive.is_dir():
            return my_drive
    
    # Check user home if mirrored or alternative path
    user_home_gdrive = Path.home() / "Google Drive"
    if user_home_gdrive.is_dir():
        return user_home_gdrive

    return None


SUBDIRECTORIES = [
    "00_References",
    "01_Source_Code",
    "02_Datasets",
    "03_Knowledge_Base",
    "04_Models_and_Embeddings",
    "05_Vector_Database_Backups",
    "06_Test_Results",
    "07_Documentation",
    "08_Reports",
    "09_Presentations",
    "10_Deployment",
    "11_Backups",
]


def setup_drive_structure(drive_root: Path):
    """Create the project structure in Google Drive."""
    project_dir = drive_root / "Internship_RAG_MCP_Capstone"
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Google Drive project root: {project_dir}")

    for sub in SUBDIRECTORIES:
        sub_path = project_dir / sub
        sub_path.mkdir(parents=True, exist_ok=True)
        # Create a small README/keepfile if empty
        keep_file = sub_path / ".keep"
        if not any(sub_path.iterdir()):
            keep_file.write_text(f"Persistent folder: {sub}\n", encoding="utf-8")
        print(f"  + {sub}/ verified.")

    return project_dir


def copy_reference_pdfs(dest_references_dir: Path):
    """Copy the discovered internship reference PDFs to 00_References."""
    downloads_dir = Path.home() / "Downloads"
    pdf_mapping = {
        "Capstone project.pdf": "Capstone_Project_Guide.pdf",
        "Internship project.pdf": "Internship_Project_Specification.pdf",
        "Enterprise AI Engineering_ RAG,Vector Search & MCP Virtual Internship.pdf": "Enterprise_AI_Engineering_Overview.pdf",
    }

    copied_count = 0
    for src_name, target_name in pdf_mapping.items():
        src_path = downloads_dir / src_name
        dest_path = dest_references_dir / target_name
        if src_path.exists():
            shutil.copy2(src_path, dest_path)
            print(f"[COPIED] {src_name} -> {dest_path.name} ({src_path.stat().st_size:,} bytes)")
            copied_count += 1
        else:
            print(f"[NOTICE] Reference source not found: {src_path}")

    return copied_count


def check_disk_space():
    """Print current free space on C: drive."""
    total, used, free = shutil.disk_usage("C:\\")
    print(f"[DISK] C: Drive: Free={free / (1024**3):.2f} GB | Total={total / (1024**3):.2f} GB")


def main():
    print("=" * 60)
    print("Google Drive & Storage Setup Validator")
    print("=" * 60)
    check_disk_space()

    my_drive = find_google_drive()
    if not my_drive:
        print("[ERROR] Google Drive mount not detected. Please ensure Google Drive for Desktop is running.")
        sys.exit(1)

    print(f"[SUCCESS] Google Drive mount located at: {my_drive}")
    project_root = setup_drive_structure(my_drive)
    references_dir = project_root / "00_References"
    copy_reference_pdfs(references_dir)

    print("=" * 60)
    print("[ALL DONE] Google Drive folder hierarchy verified successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
