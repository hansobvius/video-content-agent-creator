"""
Domain models for Project State tracking and lifecycle management.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    CREATED = "CREATED"
    SPEC_VALIDATED = "SPEC_VALIDATED"
    SCRIPT_GENERATING = "SCRIPT_GENERATING"
    SCRIPT_COMPLETED = "SCRIPT_COMPLETED"
    STORYBOARD_GENERATING = "STORYBOARD_GENERATING"
    STORYBOARD_COMPLETED = "STORYBOARD_COMPLETED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    REVISION_SCRIPT_REQUESTED = "REVISION_SCRIPT_REQUESTED"
    REVISION_STORYBOARD_REQUESTED = "REVISION_STORYBOARD_REQUESTED"
    APPROVED = "APPROVED"
    FAILED = "FAILED"


class StateTransition(BaseModel):
    from_status: Optional[ProjectStatus]
    to_status: ProjectStatus
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Optional[str] = None


class VersionsMap(BaseModel):
    script: int = Field(default=0, ge=0)
    storyboard: int = Field(default=0, ge=0)
    revision: int = Field(default=0, ge=0)


class ArtifactsMap(BaseModel):
    spec: Optional[str] = None
    script_json: Optional[str] = None
    script_md: Optional[str] = None
    storyboard_json: Optional[str] = None
    storyboard_md: Optional[str] = None
    last_feedback: Optional[str] = None


class ProjectState(BaseModel):
    project_id: str
    status: ProjectStatus = ProjectStatus.CREATED
    current_stage: str = "initialization"
    versions: VersionsMap = Field(default_factory=VersionsMap)
    artifacts: ArtifactsMap = Field(default_factory=ArtifactsMap)
    history: List[StateTransition] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def transition_to(self, new_status: ProjectStatus, stage: Optional[str] = None, details: Optional[str] = None) -> None:
        transition = StateTransition(
            from_status=self.status,
            to_status=new_status,
            details=details,
        )
        self.history.append(transition)
        self.status = new_status
        if stage:
            self.current_stage = stage
        self.updated_at = datetime.now(timezone.utc).isoformat()
