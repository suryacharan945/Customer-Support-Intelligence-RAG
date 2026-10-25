"""Feedback collection & active learning loop endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["Feedback & Active Learning"])


class FeedbackSubmission(BaseModel):
    query_id: str = Field(..., description="Unique query identifier")
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    correction: Optional[str] = Field(None, description="Human provided answer correction")
    flagged_incorrect: bool = Field(False, description="Flag answer as factually incorrect or hallucinated")
    comment: Optional[str] = Field(None, description="Qualitative feedback comments")


@router.post("/", summary="Submit User / Agent Feedback")
async def submit_feedback(submission: FeedbackSubmission):
    """
    Log human feedback to continuous improvement queue and export to persistent storage.
    """
    from app.services.feedback_service import feedback_service
    try:
        result = await feedback_service.record_feedback(submission)
        return {"status": "success", "message": "Feedback recorded", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
