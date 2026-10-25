"""RAG & MCP query endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rag", tags=["RAG & MCP Query Engine"])


class QueryRequest(BaseModel):
    query: str = Field(..., description="Customer support query", json_schema_extra={"example": "How do I reset my printer to factory settings?"})
    session_id: Optional[str] = Field("default-session", description="Session identifier for conversation memory")
    user_id: Optional[str] = Field(None, description="Optional user ID for personalization")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of context passages to retrieve")


class Citation(BaseModel):
    document_source: str
    page_or_section: Optional[str] = None
    snippet: str
    relevance_score: float


class QueryResponse(BaseModel):
    query: str
    expanded_query: Optional[str] = None
    answer: str
    confidence_score: float
    citations: List[Citation]
    contexts_used: int
    execution_time_ms: float
    requires_human_clarification: bool = False


@router.post("/query", response_model=QueryResponse, summary="Execute Multi-Context RAG Query")
async def execute_rag_query(request: QueryRequest):
    """
    Execute hybrid retrieval, multi-context prompting (MCP), and LLM response synthesis.
    """
    # Placeholder routing to service layer
    from app.services.rag_service import rag_service
    try:
        response = await rag_service.process_query(
            query=request.query,
            session_id=request.session_id,
            top_k=request.top_k,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
