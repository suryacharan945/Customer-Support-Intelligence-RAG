"""RAG & Multi-Context Prompting (MCP) query endpoints supporting Baseline and Multi-Context modes."""

from typing import List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.api.deps import get_rag_service

router = APIRouter(tags=["RAG & MCP Query Engine"])


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Customer support inquiry",
        json_schema_extra={"example": "My printer cannot connect to Wi-Fi. How can I fix it, and is the repair covered by warranty?"},
    )
    session_id: Optional[str] = Field("default-session", description="Session identifier for conversation memory")
    user_id: Optional[str] = Field(None, description="Optional user ID for personalization")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of context passages to retrieve")
    retrieval_mode: Optional[str] = Field(
        "multi_context",
        description="RAG retrieval mode: 'baseline' (dense single-channel) or 'multi_context' (MCP multi-category hybrid)",
    )


class Citation(BaseModel):
    document_source: str = Field(..., description="Source document filename or identifier")
    page_or_section: Optional[str] = Field(None, description="Section or page metadata if available")
    snippet: str = Field(..., description="Retrieved excerpt text")
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)")
    category: Optional[str] = Field("general", description="Document category (e.g. troubleshooting, warranty)")
    chunk_id: Optional[str] = Field(None, description="Exact chunk ID")
    is_verified: bool = Field(True, description="True if citation was verified against retrieved context")


class QueryResponse(BaseModel):
    query: str
    expanded_query: Optional[str] = None
    answer: str
    retrieval_mode: str = Field("multi_context", description="'baseline' or 'multi_context'")
    selected_categories: List[str] = Field(default_factory=list, description="Categories selected during query analysis")
    supporting_citations: List[Citation] = Field(default_factory=list, description="Verified citations supporting the answer")
    evidence_status: str = Field("SUFFICIENT", description="'SUFFICIENT', 'PARTIAL', or 'INSUFFICIENT'")
    retrieval_latency_ms: float = Field(0.0, description="Retrieval latency in milliseconds")
    generation_latency_ms: Optional[float] = Field(None, description="LLM generation latency in milliseconds")
    provider_status: str = Field("READY_FOR_COLAB_INFERENCE", description="Inference provider connectivity status")
    
    # Backward compatibility fields for Stage 1-3 test suite
    evidence_found: bool = Field(True, description="Whether matching context was retrieved")
    citations: List[Citation] = Field(default_factory=list, description="Retrieved citation candidates from knowledge base")
    retrieval_similarity: Optional[float] = Field(
        None,
        description="Mean relevance score of retrieved passages. Uncalibrated similarity only, not correctness probability.",
    )
    confidence_score: Optional[float] = Field(
        None,
        description="(Optional) Calibrated confidence probability. None until calibrated scoring model is integrated.",
    )
    contexts_used: int = Field(0, description="Number of context passages provided to prompt")
    execution_time_ms: float = Field(0.0, description="Total end-to-end request latency in milliseconds")
    requires_human_clarification: bool = Field(False, description="Flag indicating if confidence falls below threshold")
    is_mock: bool = Field(False, description="Flag indicating if output was generated via explicit test mock mode")


@router.post("/rag/query", response_model=QueryResponse, summary="Execute RAG Query (Legacy Route)")
@router.post("/query", response_model=QueryResponse, summary="Execute RAG Query (Standard Route)")
async def execute_rag_query(
    request: QueryRequest,
    service: Any = Depends(get_rag_service),
):
    """
    Execute end-to-end RAG query in either 'baseline' or 'multi_context' (MCP) mode.
    Returns clear HTTP errors when backends fail, avoiding silent mock fallbacks.
    """
    from app.retrieval.vector_store import VectorStoreNotInitializedError, VectorStoreQueryError
    from app.generation.llm_client import (
        ProviderNotImplementedError,
        ProviderNotConfiguredError,
        RemoteInferenceTimeoutError,
        RemoteInferenceError,
    )

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=422, detail="Query text cannot be empty or whitespace only.")

    mode = request.retrieval_mode.lower() if request.retrieval_mode else "multi_context"
    if mode not in ("baseline", "multi_context"):
        mode = "multi_context"

    try:
        response = await service.process_query(
            query=request.query.strip(),
            session_id=request.session_id or "default-session",
            top_k=request.top_k or 5,
            retrieval_mode=mode,
        )
        return response
    except VectorStoreNotInitializedError as e:
        raise HTTPException(status_code=503, detail=f"Vector store unavailable: {str(e)}")
    except VectorStoreQueryError as e:
        raise HTTPException(status_code=502, detail=f"Vector database query failed: {str(e)}")
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=f"LLM provider configuration error: {str(e)}")
    except ProviderNotImplementedError as e:
        raise HTTPException(status_code=501, detail=f"LLM provider not implemented: {str(e)}")
    except RemoteInferenceTimeoutError as e:
        raise HTTPException(status_code=504, detail=f"Remote LLM inference timeout: {str(e)}")
    except RemoteInferenceError as e:
        raise HTTPException(status_code=502, detail=f"Remote LLM inference error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal RAG pipeline error: {str(e)}")
