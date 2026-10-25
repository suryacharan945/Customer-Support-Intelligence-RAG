"""Document loading subsystem supporting multi-format customer support assets."""

import os
from pathlib import Path
from typing import Dict, List, Any


class Document:
    """Standardized internal representation of an ingested document."""
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata

    def __repr__(self):
        return f"<Document source={self.metadata.get('source')} length={len(self.content)}>"


class DocumentLoader:
    """Loads documents from persistent Google Drive knowledge base."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv"}

    def __init__(self, knowledge_base_dir: str):
        self.kb_path = Path(knowledge_base_dir)

    def load_all(self) -> List[Document]:
        """Scan knowledge base directory and parse documents."""
        documents = []
        if not self.kb_path.exists():
            return documents

        for root, _, files in os.walk(self.kb_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    file_path = Path(root) / file
                    try:
                        text = file_path.read_text(encoding="utf-8", errors="replace")
                        doc = Document(
                            content=text,
                            metadata={
                                "source": file,
                                "path": str(file_path),
                                "category": Path(root).name,
                                "size_bytes": file_path.stat().st_size,
                            },
                        )
                        documents.append(doc)
                    except Exception as e:
                        print(f"[LOADER WARNING] Failed to read {file_path}: {e}")

        return documents
