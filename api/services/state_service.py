"""
Service responsible for project state management and lifecycle transitions.
"""
import json
from pathlib import Path
from typing import Optional, Union

from api.domain.project_state import ProjectState, ProjectStatus
from api.services.project_service import ProjectService


class StateService:
    def __init__(self, project_service: Optional[ProjectService] = None):
        self.project_service = project_service or ProjectService()

    def get_state(self, project_id: str) -> ProjectState:
        state_file = self.project_service.get_state_file(project_id)
        if not state_file.exists():
            raise FileNotFoundError(f"State file not found for project {project_id}")
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectState.model_validate(data)

    def init_state(self, project_id: str, spec_rel_path: str = "VIDEO_SPEC.yaml") -> ProjectState:
        self.project_service.init_project_structure(project_id)
        state = ProjectState(
            project_id=project_id,
            status=ProjectStatus.CREATED,
            current_stage="created",
        )
        state.artifacts.spec = spec_rel_path
        self.save_state(state)
        return state

    def save_state(self, state: ProjectState) -> Path:
        state_file = self.project_service.get_state_file(state.project_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))
        return state_file

    def transition(
        self,
        project_id: str,
        new_status: ProjectStatus,
        stage: Optional[str] = None,
        details: Optional[str] = None,
    ) -> ProjectState:
        state = self.get_state(project_id)
        state.transition_to(new_status=new_status, stage=stage, details=details)
        self.save_state(state)
        return state

    def update_script_artifact(self, project_id: str, version: int) -> ProjectState:
        state = self.get_state(project_id)
        state.versions.script = version
        state.artifacts.script_json = f"scripts/script_v{version}.json"
        state.artifacts.script_md = f"scripts/script_v{version}.md"
        self.save_state(state)
        return state

    def update_storyboard_artifact(self, project_id: str, version: int) -> ProjectState:
        state = self.get_state(project_id)
        state.versions.storyboard = version
        state.artifacts.storyboard_json = f"storyboards/storyboard_v{version}.json"
        state.artifacts.storyboard_md = f"storyboards/storyboard_v{version}.md"
        self.save_state(state)
        return state

    def update_feedback_artifact(self, project_id: str, revision_number: int) -> ProjectState:
        state = self.get_state(project_id)
        state.versions.revision = revision_number
        num_str = f"{revision_number:03d}"
        state.artifacts.last_feedback = f"feedback/revision_{num_str}.json"
        self.save_state(state)
        return state
