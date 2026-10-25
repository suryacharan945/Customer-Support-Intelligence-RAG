"""RAG & MCP query endpoints with strict exception handling and uncalibrated metric isolation."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rag", tags=["RAG & MCP Query Engine"])


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Customer support query",
        json_schema_extra={"example": "How do I reset my printer to factory settings?"},
    )
    session_id: Optional[str] = Field("default-session", description="Session identifier for conversation memory")
    user_id: Optional[str] = Field(None, description="Optional user ID for personalization")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of context passages to retrieve")


class Citation(BaseModel):
    document_source: str = Field(..., description="Source document filename or identifier")
    page_or_section: Optional[str] = Field(None, description="Section or page metadata if available")
    snippet: str = Field(..., description="Retrieved excerpt text")
    relevance_score: float = Field(..., description="Hybrid retrieval relevance score (0.0 to 1.0)")


class QueryResponse(BaseModel):
    query: str
    expanded_query: Optional[str] = None
    answer: str
    evidence_found: bool = Field(True, description="Whether matching context was retrieved")
    citations: List[Citation] = Field(default_factory=list, description="Retrieved citation candidates from the knowledge base")
    retrieval_similarity: Optional[float] = Field(
        None,
        description="Mean relevance score of retrieved passages. Uncalibrated similarity only, not correctness probability.",
    )
    confidence_score: Optional[float] = Field(
        None,
        description="(Optional) Calibrated confidence probability. None until calibrated scoring model is integrated.",
    )
    contexts_used: int
    execution_time_ms: float
    requires_human_clarification: bool = False
    is_mock: bool = Field(False, description="Flag indicating if output was generated via explicit test mock mode")


@router.post("/query", response_model=QueryResponse, summary="Execute Multi-Context RAG Query")
async def execute_rag_query(request: QueryRequest):
    """
    Execute hybrid retrieval, multi-context prompting (MCP), and LLM response synthesis.
    Returns clear HTTP errors when backends fail, avoiding silent mock fallbacks.
    """
    from app.services.rag_service import rag_service
    from app.retrieval.vector_store import VectorStoreNotInitializedError, VectorStoreQueryError
    from app.generation.llm_client import (
        ProviderNotImplementedError,
        ProviderNotConfiguredError,
        RemoteInferenceTimeoutError,
        RemoteInferenceError,
    )

    try:
        response = await rag_service.process_query(
            query=request.query,
            session_id=request.session_id,
            top_k=request.top_k,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal RAG pipeline error: {str(e)}")
