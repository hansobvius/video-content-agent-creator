"""
Service responsible for project directories and filesystem structure.
"""
from pathlib import Path
from typing import Union


class ProjectService:
    def __init__(self, base_dir: Union[str, Path] = "projects"):
        self.base_dir = Path(base_dir)

    def get_project_dir(self, project_id: str) -> Path:
        return self.base_dir / project_id

    def get_scripts_dir(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "scripts"

    def get_storyboards_dir(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "storyboards"

    def get_feedback_dir(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "feedback"

    def get_logs_dir(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "logs"

    def get_state_file(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "state.json"

    def get_spec_file(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "VIDEO_SPEC.yaml"

    def project_exists(self, project_id: str) -> bool:
        return self.get_project_dir(project_id).exists() and self.get_state_file(project_id).exists()

    def init_project_structure(self, project_id: str) -> Path:
        """
        Creates the project directory and standard subdirectories.
        """
        project_dir = self.get_project_dir(project_id)
        self.get_scripts_dir(project_id).mkdir(parents=True, exist_ok=True)
        self.get_storyboards_dir(project_id).mkdir(parents=True, exist_ok=True)
        self.get_feedback_dir(project_id).mkdir(parents=True, exist_ok=True)
        self.get_logs_dir(project_id).mkdir(parents=True, exist_ok=True)
        return project_dir
