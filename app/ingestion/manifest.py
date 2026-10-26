"""Persistent Ingestion Manifest for deterministic duplicate detection and document versioning."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


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

    def register_document(
        self,
        doc_dict: Dict[str, Any],
        chunk_count: int,
        lifecycle_status: str = "pending_index",
    ) -> Dict[str, Any]:
        """
        Record a successfully processed document into the manifest.
        Updates version history if the document was modified.
        Tracks lifecycle status across 6 states: uploaded, processed, pending_index, indexed, indexing_failed, deleted.
        Never marks a document as searchable until it is indexed.
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

        is_searchable = (lifecycle_status == "indexed")
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
            "status": "ACTIVE" if lifecycle_status != "deleted" else "DELETED",
            "lifecycle_status": lifecycle_status,
            "is_searchable": is_searchable,
        }

        self.manifest_data["documents"][content_hash] = doc_record
        self.save()
        return doc_record

    def _normalize_lifecycle(self, doc: Dict[str, Any]):
        """Ensure legacy manifest records have consistent lifecycle fields."""
        if "lifecycle_status" not in doc:
            if doc.get("status") == "DELETED":
                doc["lifecycle_status"] = "deleted"
            else:
                doc["lifecycle_status"] = "indexed"
        doc["is_searchable"] = (doc.get("lifecycle_status") == "indexed")

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Find active or inactive document by document_id."""
        for doc in self.manifest_data["documents"].values():
            if doc.get("document_id") == document_id:
                self._normalize_lifecycle(doc)
                return doc
        return None

    def update_lifecycle_status(
        self,
        document_id: str,
        lifecycle_status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update document lifecycle status across the 6 allowed states."""
        allowed_states = {
            "uploaded",
            "processed",
            "pending_index",
            "indexed",
            "indexing_failed",
            "deleted",
        }
        if lifecycle_status not in allowed_states:
            raise ValueError(f"Invalid lifecycle status '{lifecycle_status}'. Allowed: {allowed_states}")

        doc = self.get_document_by_id(document_id)
        if not doc:
            return False

        doc["lifecycle_status"] = lifecycle_status
        doc["is_searchable"] = (lifecycle_status == "indexed")
        doc["last_seen"] = datetime.now(timezone.utc).isoformat()
        if error_message:
            doc["error_message"] = error_message
        if lifecycle_status == "deleted":
            doc["status"] = "DELETED"
            doc["deleted_at"] = doc["last_seen"]

        self.save()
        return True

    def mark_deleted(self, document_id: str) -> bool:
        """Atomically mark document as deleted in manifest."""
        return self.update_lifecycle_status(document_id, "deleted")

    def list_documents(
        self,
        category: Optional[str] = None,
        include_deleted: bool = False,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List documents matching category and lifecycle filters."""
        results = []
        for doc in self.manifest_data["documents"].values():
            self._normalize_lifecycle(doc)
            if not include_deleted and (doc.get("status") == "DELETED" or doc.get("lifecycle_status") == "deleted"):
                continue
            if category and doc.get("category") != category:
                continue
            if status and doc.get("lifecycle_status") != status:
                continue
            results.append(dict(doc))
        return results

    def get_status_summary(self) -> Dict[str, Any]:
        """Aggregate knowledge base statistics across categories and lifecycle states."""
        by_category: Dict[str, int] = {}
        by_status: Dict[str, int] = {
            "uploaded": 0,
            "processed": 0,
            "pending_index": 0,
            "indexed": 0,
            "indexing_failed": 0,
            "deleted": 0,
        }
        total_chunks = 0
        active_count = 0

        for doc in self.manifest_data["documents"].values():
            self._normalize_lifecycle(doc)
            l_status = doc.get("lifecycle_status", "indexed")
            by_status[l_status] = by_status.get(l_status, 0) + 1

            if l_status != "deleted" and doc.get("status") != "DELETED":
                cat = doc.get("category", "general")
                by_category[cat] = by_category.get(cat, 0) + 1
                total_chunks += doc.get("chunk_count", 0)
                active_count += 1

        return {
            "total_documents": active_count,
            "total_active_chunks": total_chunks,
            "by_category": by_category,
            "by_lifecycle_status": by_status,
            "searchable_documents_count": by_status.get("indexed", 0),
        }
