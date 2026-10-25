"""Persistent Ingestion Manifest for deterministic duplicate detection and document versioning."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class IngestionManifest:
    """
    Manages persistent record of ingested files to prevent duplicate processing
    and track content versioning across application restarts.
    """

    def __init__(self, manifest_path: Optional[str | Path] = None):
        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.manifest_data: Dict[str, Any] = {
            "manifest_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "documents": {},      # content_hash -> document record
            "file_registry": {},  # "category:filename" -> {latest_hash, version, history}
        }
        if self.manifest_path and self.manifest_path.exists():
            self.load()

    def load(self):
        """Load manifest from disk."""
        if not self.manifest_path or not self.manifest_path.exists():
            return
        try:
            content = self.manifest_path.read_text(encoding="utf-8")
            self.manifest_data = json.loads(content)
        except Exception as e:
            print(f"[MANIFEST WARNING] Failed to load manifest at {self.manifest_path}: {e}")

    def save(self):
        """Atomically persist manifest to disk via temporary write and replace."""
        if not self.manifest_path:
            return

        self.manifest_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = self.manifest_path.parent
        with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
            json.dump(self.manifest_data, tf, indent=2, ensure_ascii=False)
            temp_name = tf.name

        os.replace(temp_name, str(self.manifest_path))

    def evaluate_file(self, category: str, filename: str, content_hash: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Evaluate if a file is NEW, UNCHANGED (duplicate), or MODIFIED (new content version).
        Returns:
            ("UNCHANGED", existing_record) -> Content identical, skip re-chunking.
            ("MODIFIED", previous_record)  -> Same filename, but content hash changed.
            ("NEW", None)                  -> First time seeing this file.
        """
        key = f"{category}:{filename}"
        reg_entry = self.manifest_data["file_registry"].get(key)

        if not reg_entry:
            # Check if identical hash exists under another name
            existing_doc = self.manifest_data["documents"].get(content_hash)
            if existing_doc:
                return ("CONTENT_EXISTS_DIFFERENT_NAME", existing_doc)
            return ("NEW", None)

        if reg_entry.get("latest_content_hash") == content_hash:
            existing_doc = self.manifest_data["documents"].get(content_hash)
            return ("UNCHANGED", existing_doc)

        # File exists under this key but hash has changed
        prev_hash = reg_entry.get("latest_content_hash")
        prev_doc = self.manifest_data["documents"].get(prev_hash)
        return ("MODIFIED", prev_doc)

    def register_document(self, doc_dict: Dict[str, Any], chunk_count: int) -> Dict[str, Any]:
        """
        Record a successfully processed document into the manifest.
        Updates version history if the document was modified.
        """
        category = doc_dict["category"]
        filename = doc_dict["filename"]
        content_hash = doc_dict["content_hash"]
        key = f"{category}:{filename}"
        timestamp = datetime.now(timezone.utc).isoformat()

        reg_entry = self.manifest_data["file_registry"].get(key)
        if reg_entry:
            if reg_entry.get("latest_content_hash") == content_hash:
                version = reg_entry.get("version", 1)
            else:
                version = reg_entry.get("version", 1) + 1
                reg_entry["version"] = version
                reg_entry["latest_content_hash"] = content_hash
                reg_entry["history"].append({"version": version, "content_hash": content_hash, "timestamp": timestamp})
        else:
            version = 1
            self.manifest_data["file_registry"][key] = {
                "latest_content_hash": content_hash,
                "version": version,
                "history": [{"version": version, "content_hash": content_hash, "timestamp": timestamp}],
            }

        doc_record = {
            "document_id": doc_dict["document_id"],
            "filename": filename,
            "category": category,
            "document_type": doc_dict["document_type"],
            "content_hash": content_hash,
            "version": version,
            "file_size_bytes": doc_dict.get("file_size_bytes", 0),
            "total_pages": doc_dict.get("total_pages"),
            "chunk_count": chunk_count,
            "first_ingested": doc_dict.get("ingestion_timestamp", timestamp),
            "last_seen": timestamp,
            "status": "ACTIVE",
        }

        self.manifest_data["documents"][content_hash] = doc_record
        self.save()
        return doc_record
