"""
Domain models for Human Revision Feedback.
"""
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class RevisionTarget(str, Enum):
    SCRIPT = "script"
    STORYBOARD = "storyboard"


class RevisionFeedback(BaseModel):
    project_id: str = Field(..., description="Target project ID")
    revision_number: int = Field(default=1, ge=1, description="Sequential revision index")
    target: RevisionTarget = Field(..., description="Target artifact to revise ('script' or 'storyboard')")
    feedback: str = Field(..., min_length=3, description="Human instruction/feedback for the agent")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of feedback creation"
    )
