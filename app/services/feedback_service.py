"""Continuous Learning & Human-in-the-Loop Feedback Service."""

import json
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.api.endpoints.feedback import FeedbackSubmission
from app.core.config import settings
from app.core.logging import logger


class FeedbackService:
    """Stores user feedback for active learning dataset refinement."""

    def __init__(self):
        self.gdrive_root = Path(settings.GOOGLE_DRIVE_ROOT)

    async def record_feedback(self, submission: Any) -> Dict[str, Any]:
        """Log submission to in-memory queue and persist to Google Drive if connected."""
        feedback_record = {
            "query_id": submission.query_id,
            "rating": submission.rating,
            "correction": submission.correction,
            "flagged_incorrect": submission.flagged_incorrect,
            "comment": submission.comment,
        }

        logger.info(f"Recorded feedback for Query ID {submission.query_id}: rating={submission.rating}")

        # If Google Drive is mounted, persist to 06_Test_Results / feedback log
        if self.gdrive_root.exists():
            feedback_file = self.gdrive_root / "06_Test_Results" / "user_feedback_log.jsonl"
            try:
                with open(feedback_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(feedback_record) + "\n")
            except Exception as e:
                logger.warning(f"Could not write feedback to Google Drive: {e}")

        return feedback_record


feedback_service = FeedbackService()
