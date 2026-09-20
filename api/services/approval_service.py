"""
Service responsible for Human-in-the-Loop approval and granular revision requests.
"""
from typing import Optional

from api.domain.feedback import RevisionFeedback, RevisionTarget
from api.domain.project_state import ProjectStatus
from api.services.artifact_service import ArtifactService
from api.services.state_service import StateService


class ApprovalService:
    def __init__(
        self,
        state_service: Optional[StateService] = None,
        artifact_service: Optional[ArtifactService] = None,
    ):
        self.state_service = state_service or StateService()
        self.artifact_service = artifact_service or ArtifactService()

    def approve(self, project_id: str) -> dict:
        state = self.state_service.get_state(project_id)
        if state.status != ProjectStatus.AWAITING_APPROVAL:
            raise ValueError(f"Cannot approve project in status '{state.status.value}'. Must be 'AWAITING_APPROVAL'.")

        self.state_service.transition(
            project_id=project_id,
            new_status=ProjectStatus.APPROVED,
            stage="completed",
            details="Approved by human reviewer.",
        )
        return {
            "project_id": project_id,
            "status": "APPROVED",
            "message": "Project production plan has been successfully approved.",
        }

    def request_revision(
        self,
        project_id: str,
        target: RevisionTarget,
        feedback_text: str,
    ) -> RevisionFeedback:
        state = self.state_service.get_state(project_id)
        if state.status not in (ProjectStatus.AWAITING_APPROVAL, ProjectStatus.APPROVED):
            raise ValueError(f"Cannot request revision in status '{state.status.value}'. Must be 'AWAITING_APPROVAL' or 'APPROVED'.")

        next_revision = state.versions.revision + 1
        feedback_record = RevisionFeedback(
            project_id=project_id,
            revision_number=next_revision,
            target=target,
            feedback=feedback_text,
        )

        # Save feedback artifact
        self.artifact_service.save_feedback(feedback_record)
        self.state_service.update_feedback_artifact(project_id, next_revision)

        # Transition status according to granular target
        new_status = (
            ProjectStatus.REVISION_SCRIPT_REQUESTED
            if target == RevisionTarget.SCRIPT
            else ProjectStatus.REVISION_STORYBOARD_REQUESTED
        )

        self.state_service.transition(
            project_id=project_id,
            new_status=new_status,
            stage=f"revision_{target.value}",
            details=f"Revision requested for {target.value}: {feedback_text[:50]}...",
        )

        return feedback_record
