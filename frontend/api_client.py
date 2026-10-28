"""FastAPI Backend HTTP Client for Streamlit Frontend.

Provides a robust, decoupled, and typed interface to the FastAPI backend.
Enforces:
- Strict error handling (never silences errors or injects mocks)
- Configurable base URL and timeouts
- Safe retries ONLY on idempotent GET operations
- Absolute prevention of duplicate uploads (zero retries on file upload POSTs)
- No direct database or ChromaDB access
"""

import os
import time
from typing import Dict, Any, List, Optional
import httpx


class APIClientError(Exception):
    """Base exception for all API client errors."""
    pass


class APIConnectionError(APIClientError):
    """Raised when the FastAPI backend is completely offline or unreachable."""
    pass


class APITimeoutError(APIClientError):
    """Raised when an API request exceeds the configured timeout threshold."""
    pass


class APIStatusError(APIClientError):
    """Raised when the API returns an HTTP 4xx or 5xx error."""
    def __init__(self, status_code: int, detail: str, response_json: Optional[Dict[str, Any]] = None):
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail
        self.response_json = response_json or {}


class APIClient:
    """HTTP client communicating with the Customer Support Intelligence Assistant API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 15.0,
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the FastAPI service. Defaults to FASTAPI_BASE_URL env or http://127.0.0.1:8000.
            timeout: Request timeout in seconds.
        """
        env_url = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
        self.base_url = (base_url or env_url).rstrip("/")
        self.timeout = timeout

    def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 1,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute an idempotent GET request with optional safe retry on connection failure.
        """
        url = f"{self.base_url}{endpoint}"
        last_exception = None
        req_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=req_timeout) as client:
                    response = client.get(url, params=params)
                    return self._handle_response(response)
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(0.2)
                    continue
                raise APIConnectionError(
                    f"Unable to connect to FastAPI backend at {self.base_url}. "
                    f"Ensure the server is running on the expected host/port. Detail: {str(e)}"
                ) from e
            except httpx.TimeoutException as e:
                raise APITimeoutError(
                    f"Request to '{endpoint}' timed out after {req_timeout}s."
                ) from e
            except httpx.RequestError as e:
                raise APIClientError(f"Network request error: {str(e)}") from e

        if last_exception:
            raise APIConnectionError(f"Connection failed after retries: {str(last_exception)}")

    def _post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_idempotent: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a POST request.
        Strictly disables retries for non-idempotent operations (such as document uploads).
        """
        url = f"{self.base_url}{endpoint}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if files:
                    # Multipart file upload
                    response = client.post(url, data=data, files=files)
                else:
                    response = client.post(url, json=json_data)
                return self._handle_response(response)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise APIConnectionError(
                f"Cannot connect to FastAPI backend at {self.base_url}. Detail: {str(e)}"
            ) from e
        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"POST request to '{endpoint}' timed out after {self.timeout}s."
            ) from e
        except httpx.RequestError as e:
            raise APIClientError(f"Network error during POST '{endpoint}': {str(e)}") from e

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        """Execute a DELETE request."""
        url = f"{self.base_url}{endpoint}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.delete(url)
                return self._handle_response(response)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise APIConnectionError(
                f"Cannot connect to FastAPI backend at {self.base_url}. Detail: {str(e)}"
            ) from e
        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"DELETE request to '{endpoint}' timed out after {self.timeout}s."
            ) from e
        except httpx.RequestError as e:
            raise APIClientError(f"Network error during DELETE '{endpoint}': {str(e)}") from e

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process HTTP response and raise structured exceptions for errors."""
        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text or f"HTTP {response.status_code}"}

        if response.status_code >= 400:
            detail = data.get("detail", f"Error {response.status_code}")
            if isinstance(detail, list):
                # Pydantic validation error list
                detail = "; ".join(f"{item.get('loc', '')}: {item.get('msg', '')}" for item in detail)
            raise APIStatusError(
                status_code=response.status_code,
                detail=str(detail),
                response_json=data if isinstance(data, dict) else {},
            )

        return data

    # --------------------------------------------------------------------------
    # Health & Readiness Diagnostics
    # --------------------------------------------------------------------------

    def get_health(self, timeout: float = 1.5) -> Dict[str, Any]:
        """Retrieve fast system liveness metrics and storage status."""
        return self._get("/api/v1/health", max_retries=0, timeout=timeout)

    def get_ready(self, timeout: float = 2.5) -> Dict[str, Any]:
        """
        Perform deep readiness check across all subsystems.
        Note: If 503 is returned, this catches the APIStatusError and returns the unready payload.
        """
        try:
            return self._get("/api/v1/ready", max_retries=0, timeout=timeout)
        except APIStatusError as e:
            if e.status_code == 503 and e.response_json:
                return e.response_json
            raise

    # --------------------------------------------------------------------------
    # RAG Query Engine
    # --------------------------------------------------------------------------

    def query(
        self,
        query: str,
        retrieval_mode: str = "multi_context",
        top_k: int = 5,
        session_id: str = "default-session",
        category: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute customer support query retrieval and generation.
        
        Args:
            query: Customer question.
            retrieval_mode: 'baseline' or 'multi_context'.
            top_k: Number of context passages (1-20).
            session_id: Optional conversation session tracking identifier.
            category: Optional category filter hint.
            llm_provider: Optional provider override ('auto', 'local', 'colab_remote').
        """
        payload: Dict[str, Any] = {
            "query": query.strip(),
            "retrieval_mode": retrieval_mode,
            "top_k": top_k,
            "session_id": session_id,
        }
        if llm_provider:
            payload["llm_provider"] = llm_provider
        return self._post("/api/v1/query", json_data=payload)

    # --------------------------------------------------------------------------
    # Document Lifecycle Management
    # --------------------------------------------------------------------------

    def list_documents(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        include_deleted: bool = False,
    ) -> Dict[str, Any]:
        """
        List registered documents from the ingestion manifest.
        
        Args:
            category: Filter by category (e.g. 'troubleshooting', 'warranty').
            status: Filter by lifecycle state ('uploaded', 'processed', 'pending_index', 'indexed', 'indexing_failed', 'deleted').
            include_deleted: Whether to include marked-deleted documents.
        """
        params: Dict[str, Any] = {"include_deleted": include_deleted}
        if category and category != "all":
            params["category"] = category
        if status and status != "all":
            params["status"] = status

        return self._get("/api/v1/documents", params=params)

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve metadata for a specific document by ID."""
        return self._get(f"/api/v1/documents/{document_id}")

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        category: str,
    ) -> Dict[str, Any]:
        """
        Upload and ingest a document.
        STRICT: Zero retries to prevent duplicate uploads.
        """
        files = {"file": (filename, file_bytes)}
        data = {"category": category}
        return self._post(
            "/api/v1/documents",
            files=files,
            data=data,
            is_idempotent=False,
        )

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Atomically delete a document across source storage, ChromaDB, and BM25 index.
        """
        return self._delete(f"/api/v1/documents/{document_id}")

    # --------------------------------------------------------------------------
    # Knowledge Base Status & Telemetry
    # --------------------------------------------------------------------------

    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """Retrieve aggregated knowledge base status across categories, indexing states, and storage."""
        return self._get("/api/v1/knowledge-base/status")

    # --------------------------------------------------------------------------
    # User Feedback
    # --------------------------------------------------------------------------

    def submit_feedback(
        self,
        query_id: str,
        rating: int,
        comment: Optional[str] = None,
        flagged_incorrect: bool = False,
        correction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit user / agent feedback on a retrieved response for active learning.
        """
        payload: Dict[str, Any] = {
            "query_id": query_id,
            "rating": rating,
            "comment": comment,
            "flagged_incorrect": flagged_incorrect,
            "correction": correction,
        }
        return self._post("/api/v1/feedback", json_data=payload)
