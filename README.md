# Internship RAG MCP Capstone Project

## 1. Storage Architecture Overview

This project implements a **Google Drive First, Minimal Local Storage** policy to ensure high efficiency on limited local storage while leveraging ~5 TB of Google Cloud storage (`suryacharan5555@gmail.com`).

- **Cloud Storage (Persistent)**: `G:\My Drive\Internship_RAG_MCP_Capstone\` (via Google Drive in **Stream files mode**).
- **Local Workspace (Ephemeral / Fast Dev)**: `C:\Users\surya\Internship_RAG_MCP_Capstone\` (~1.5–2.0 GB maximum).

---

## 2. Google Drive Directory Structure

```
Internship_RAG_MCP_Capstone/
├── 00_References/                 # Project PDFs & official guides
├── 01_Source_Code/                # Regular source-code release archives
├── 02_Datasets/                   # Raw and processed datasets
├── 03_Knowledge_Base/             # Unstructured documents, manuals, knowledge files
├── 04_Models_and_Embeddings/      # Saved embeddings & model weights
├── 05_Vector_Database_Backups/    # ChromaDB snapshots & dumps
├── 06_Test_Results/               # Evaluation results, benchmark metrics
├── 07_Documentation/              # System architecture, API documentation
├── 08_Reports/                    # Progress reports, milestone reviews
├── 09_Presentations/              # Slides and defense visual decks
├── 10_Deployment/                 # Dockerfiles, deployment manifests
└── 11_Backups/                    # Timestamped full-project archives
```

---

## 3. Important Storage Rules

1. **Stream files mode ONLY**: Google Drive for Desktop must remain in **Stream files** mode. Never set to "Mirror files" mode to prevent cloning cloud files to the local C: disk.
2. **Local Isolation for Databases and Git**:
   - Git repository (`.git/`) resides exclusively in the local working directory.
   - ChromaDB active runtime resides in `.chroma_live/` (excluded from direct sync to avoid SQLite locking collisions).
   - Consistent database snapshots are exported to `05_Vector_Database_Backups/` using `python scripts/backup_to_drive.py`.
3. **No Heavy Models Locally**:
   - Mistral 7B will run on **Google Colab (NVIDIA T4 GPU)** or remote API.
   - Embeddings (`all-MiniLM-L6-v2`) are stored locally (~120 MB).

---

## 4. Maintenance Scripts

- **`scripts/verify_storage_and_sync.py`**: Verifies Google Drive virtual mount, ensures folder hierarchy, and checks C: drive headroom.
- **`scripts/backup_to_drive.py`**: Creates a clean, safe snapshot of source code and ChromaDB to Google Drive.
