"""Abstract retrieval base interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class RetrievalResult:
    """Standardized retrieved context unit."""
    def __init__(
        self,
        document_id: str,
        text: str,
        score: float,
        source: str,
        metadata: Dict[str, Any],
    ):
        self.document_id = document_id
        self.text = text
        self.score = score
        self.source = source
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "text": self.text,
            "score": round(self.score, 4),
            "source": self.source,
            "metadata": self.metadata,
        }


class BaseRetriever(ABC):
    """Abstract interface for all retrieval implementations."""

    @abstractmethod
    def retrieve(
        self, query: str, top_k: int = 5, category: Optional[str] = None
    ) -> List[RetrievalResult]:
        """Retrieve top_k matching documents for a given query, optionally filtered by category."""
        pass
