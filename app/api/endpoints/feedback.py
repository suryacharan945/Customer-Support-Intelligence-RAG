"""Feedback collection & active learning loop endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.api.deps import get_feedback_service
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback & Active Learning"])


class FeedbackSubmission(BaseModel):
    query_id: str = Field(..., description="Unique query identifier")
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    correction: Optional[str] = Field(None, description="Human provided answer correction")
    flagged_incorrect: bool = Field(False, description="Flag answer as factually incorrect or hallucinated")
    comment: Optional[str] = Field(None, description="Qualitative feedback comments")


@router.post("", summary="Submit User / Agent Feedback")
@router.post("/", summary="Submit User / Agent Feedback (Alias)")
async def submit_feedback(
    submission: FeedbackSubmission,
    service: FeedbackService = Depends(get_feedback_service),
):
    """
    Log human feedback to continuous improvement queue and export to persistent storage.
    """
    try:
        result = await service.record_feedback(submission)
        return {"status": "success", "message": "Feedback recorded", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
