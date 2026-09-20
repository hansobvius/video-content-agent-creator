"""
VideoProductionAgent: Main orchestrator controlling the video production workflow.
"""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Optional, Union
import yaml

from api.agents.script.agent import ScriptAgent
from api.agents.storyboard.agent import StoryboardAgent
from api.domain.feedback import RevisionFeedback, RevisionTarget
from api.domain.project_state import ProjectState, ProjectStatus
from api.domain.video_spec import VideoSpec
from api.services.approval_service import ApprovalService
from api.services.artifact_service import ArtifactService
from api.services.llm_service import LLMService
from api.services.project_service import ProjectService
from api.services.state_service import StateService


class VideoProductionAgent:
    def __init__(
        self,
        project_service: Optional[ProjectService] = None,
        artifact_service: Optional[ArtifactService] = None,
        state_service: Optional[StateService] = None,
        approval_service: Optional[ApprovalService] = None,
        script_agent: Optional[ScriptAgent] = None,
        storyboard_agent: Optional[StoryboardAgent] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.project_service = project_service or ProjectService()
        self.artifact_service = artifact_service or ArtifactService(self.project_service)
        self.state_service = state_service or StateService(self.project_service)
        self.approval_service = approval_service or ApprovalService(self.state_service, self.artifact_service)
        self.llm_service = llm_service or LLMService()

        self.script_agent = script_agent or ScriptAgent(llm_service=self.llm_service)
        self.storyboard_agent = storyboard_agent or StoryboardAgent(llm_service=self.llm_service)

    def _log_execution(self, project_id: str, agent_name: str, status: str, details: dict) -> None:
        log_dir = self.project_service.get_logs_dir(project_id)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "execution.log"

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id,
            "agent": agent_name,
            "model": getattr(self.llm_service, "model_name", "mock"),
            "status": status,
            **details,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def run(self, spec_path: Union[str, Path]) -> ProjectState:
        """
        Executes initial pipeline from a VIDEO_SPEC yaml file.
        """
        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")

        with open(spec_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        # 1. Validate spec
        is_valid, errors, spec = VideoSpec.validate_raw_dict(raw_data)
        if not is_valid or spec is None:
            raise ValueError(f"Invalid VIDEO_SPEC: {errors}")

        project_id = spec.project.id

        # 2. Init project structure and state
        self.project_service.init_project_structure(project_id)
        self.artifact_service.save_video_spec(project_id, spec)
        state = self.state_service.init_state(project_id)
        state = self.state_service.transition(
            project_id=project_id,
            new_status=ProjectStatus.SPEC_VALIDATED,
            stage="spec_validated",
            details="VIDEO_SPEC validated and saved successfully.",
        )
        self._log_execution(project_id, "VideoProductionAgent", "SUCCESS", {"stage": "spec_validation"})

        try:
            # 3. Execute ScriptAgent (v1)
            self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.SCRIPT_GENERATING,
                stage="script_generation",
            )
            script = self.script_agent.generate(spec=spec, version=1)
            json_p, md_p = self.artifact_service.save_script(script)
            self.state_service.update_script_artifact(project_id, version=1)
            self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.SCRIPT_COMPLETED,
                stage="script_completed",
                details=f"Script v1 generated with {script.total_scenes} scenes.",
            )
            self._log_execution(
                project_id,
                "ScriptAgent",
                "SUCCESS",
                {"output_json": str(json_p), "scenes": script.total_scenes},
            )

            # 4. Execute StoryboardAgent (v1)
            self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.STORYBOARD_GENERATING,
                stage="storyboard_generation",
            )
            storyboard = self.storyboard_agent.generate(script=script, version=1)
            s_json_p, s_md_p = self.artifact_service.save_storyboard(storyboard)
            self.state_service.update_storyboard_artifact(project_id, version=1)
            self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.STORYBOARD_COMPLETED,
                stage="storyboard_completed",
                details=f"Storyboard v1 generated with {storyboard.total_scenes} scenes.",
            )
            self._log_execution(
                project_id,
                "StoryboardAgent",
                "SUCCESS",
                {"output_json": str(s_json_p), "scenes": storyboard.total_scenes},
            )

            # 5. Pause for Human Approval
            state = self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.AWAITING_APPROVAL,
                stage="awaiting_approval",
                details="Pipeline paused. Awaiting human review.",
            )
            self._log_execution(project_id, "VideoProductionAgent", "PAUSED", {"status": "AWAITING_APPROVAL"})
            return state

        except Exception as e:
            self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.FAILED,
                stage="failed",
                details=f"Execution error: {str(e)}",
            )
            self._log_execution(project_id, "VideoProductionAgent", "FAILED", {"error": str(e)})
            raise

    def process_revision(
        self,
        project_id: str,
        target: RevisionTarget,
        feedback_text: str,
    ) -> ProjectState:
        """
        Executes granular revision based on the target (script vs storyboard).
        """
        state = self.state_service.get_state(project_id)
        spec = self.artifact_service.load_video_spec(project_id)

        # 1. Register feedback and transition state
        feedback_record = self.approval_service.request_revision(
            project_id=project_id,
            target=target,
            feedback_text=feedback_text,
        )
        self._log_execution(
            project_id,
            "ApprovalService",
            "REVISION_REQUESTED",
            {"target": target.value, "feedback": feedback_text},
        )

        try:
            if target == RevisionTarget.SCRIPT:
                # Scenario 1: Re-generate Script + Storyboard
                current_script_version = state.versions.script
                new_script_version = current_script_version + 1
                previous_script = self.artifact_service.load_script(project_id, current_script_version)

                # Generate revised script
                self.state_service.transition(
                    project_id=project_id,
                    new_status=ProjectStatus.SCRIPT_GENERATING,
                    stage="script_revising",
                )
                revised_script = self.script_agent.generate(
                    spec=spec,
                    version=new_script_version,
                    previous_script=previous_script,
                    feedback=feedback_record,
                )
                self.artifact_service.save_script(revised_script)
                self.state_service.update_script_artifact(project_id, new_script_version)
                self.state_service.transition(
                    project_id=project_id,
                    new_status=ProjectStatus.SCRIPT_COMPLETED,
                    stage="script_revision_completed",
                )
                self._log_execution(
                    project_id,
                    "ScriptAgent",
                    "SUCCESS",
                    {"version": new_script_version, "stage": "revision"},
                )

                # Re-generate storyboard for the revised script
                current_storyboard_version = state.versions.storyboard
                new_storyboard_version = current_storyboard_version + 1
                previous_storyboard = self.artifact_service.load_storyboard(project_id, current_storyboard_version)

                self.state_service.transition(
                    project_id=project_id,
                    new_status=ProjectStatus.STORYBOARD_GENERATING,
                    stage="storyboard_revising",
                )
                revised_storyboard = self.storyboard_agent.generate(
                    script=revised_script,
                    version=new_storyboard_version,
                    previous_storyboard=previous_storyboard,
                    feedback=feedback_record,
                )
                self.artifact_service.save_storyboard(revised_storyboard)
                self.state_service.update_storyboard_artifact(project_id, new_storyboard_version)
                self.state_service.transition(
                    project_id=project_id,
                    new_status=ProjectStatus.STORYBOARD_COMPLETED,
                    stage="storyboard_revision_completed",
                )
                self._log_execution(
                    project_id,
                    "StoryboardAgent",
                    "SUCCESS",
                    {"version": new_storyboard_version, "stage": "revision_after_script"},
                )

            elif target == RevisionTarget.STORYBOARD:
                # Scenario 2: Preserves Script untouched, revises only Storyboard
                current_script_version = state.versions.script
                active_script = self.artifact_service.load_script(project_id, current_script_version)

                current_storyboard_version = state.versions.storyboard
                new_storyboard_version = current_storyboard_version + 1
                previous_storyboard = self.artifact_service.load_storyboard(project_id, current_storyboard_version)

                self.state_service.transition(
                    project_id=project_id,
                    new_status=ProjectStatus.STORYBOARD_GENERATING,
                    stage="storyboard_revising_only",
                )
                revised_storyboard = self.storyboard_agent.generate(
                    script=active_script,
                    version=new_storyboard_version,
                    previous_storyboard=previous_storyboard,
                    feedback=feedback_record,
                )
                self.artifact_service.save_storyboard(revised_storyboard)
                self.state_service.update_storyboard_artifact(project_id, new_storyboard_version)
                self.state_service.transition(
                    project_id=project_id,
                    new_status=ProjectStatus.STORYBOARD_COMPLETED,
                    stage="storyboard_revision_completed",
                )
                self._log_execution(
                    project_id,
                    "StoryboardAgent",
                    "SUCCESS",
                    {"version": new_storyboard_version, "stage": "visual_revision_only"},
                )

            # Return to Awaiting Approval
            final_state = self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.AWAITING_APPROVAL,
                stage="awaiting_approval",
                details="Revision completed. Awaiting review.",
            )
            return final_state

        except Exception as e:
            self.state_service.transition(
                project_id=project_id,
                new_status=ProjectStatus.FAILED,
                stage="failed",
                details=f"Revision error: {str(e)}",
            )
            self._log_execution(project_id, "VideoProductionAgent", "FAILED", {"error": str(e)})
            raise
