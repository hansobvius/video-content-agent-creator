"""
Service responsible for persisting, formatting, and reading versioned artifacts.
"""
import json
from pathlib import Path
from typing import Optional, Union
import yaml

from api.domain.feedback import RevisionFeedback
from api.domain.script import Script
from api.domain.storyboard import Storyboard
from api.domain.video_spec import VideoSpec
from api.services.project_service import ProjectService


class ArtifactService:
    def __init__(self, project_service: Optional[ProjectService] = None):
        self.project_service = project_service or ProjectService()

    def save_video_spec(self, project_id: str, spec: VideoSpec) -> Path:
        self.project_service.init_project_structure(project_id)
        spec_path = self.project_service.get_spec_file(project_id)
        with open(spec_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(spec.model_dump(), f, sort_keys=False, allow_unicode=True)
        return spec_path

    def load_video_spec(self, project_id: str) -> VideoSpec:
        spec_path = self.project_service.get_spec_file(project_id)
        if not spec_path.exists():
            raise FileNotFoundError(f"VIDEO_SPEC.yaml not found for project {project_id}")
        with open(spec_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return VideoSpec.model_validate(data)

    def save_script(self, script: Script) -> tuple[Path, Path]:
        project_id = script.project_id
        version = script.version
        scripts_dir = self.project_service.get_scripts_dir(project_id)
        scripts_dir.mkdir(parents=True, exist_ok=True)

        json_path = scripts_dir / f"script_v{version}.json"
        md_path = scripts_dir / f"script_v{version}.md"

        # 1. Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(script.model_dump_json(indent=2))

        # 2. Save Markdown
        md_content = self.format_script_markdown(script)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path

    def load_script(self, project_id: str, version: int) -> Script:
        json_path = self.project_service.get_scripts_dir(project_id) / f"script_v{version}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Script v{version} not found at {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Script.model_validate(data)

    def save_storyboard(self, storyboard: Storyboard) -> tuple[Path, Path]:
        project_id = storyboard.project_id
        version = storyboard.version
        storyboards_dir = self.project_service.get_storyboards_dir(project_id)
        storyboards_dir.mkdir(parents=True, exist_ok=True)

        json_path = storyboards_dir / f"storyboard_v{version}.json"
        md_path = storyboards_dir / f"storyboard_v{version}.md"

        # 1. Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(storyboard.model_dump_json(indent=2))

        # 2. Save Markdown
        md_content = self.format_storyboard_markdown(storyboard)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path

    def load_storyboard(self, project_id: str, version: int) -> Storyboard:
        json_path = self.project_service.get_storyboards_dir(project_id) / f"storyboard_v{version}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Storyboard v{version} not found at {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Storyboard.model_validate(data)

    def save_feedback(self, feedback: RevisionFeedback) -> Path:
        project_id = feedback.project_id
        feedback_dir = self.project_service.get_feedback_dir(project_id)
        feedback_dir.mkdir(parents=True, exist_ok=True)

        num_str = f"{feedback.revision_number:03d}"
        file_path = feedback_dir / f"revision_{num_str}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(feedback.model_dump_json(indent=2))
        return file_path

    def load_feedback(self, project_id: str, revision_number: int) -> RevisionFeedback:
        num_str = f"{revision_number:03d}"
        file_path = self.project_service.get_feedback_dir(project_id) / f"revision_{num_str}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Feedback revision {num_str} not found at {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return RevisionFeedback.model_validate(data)

    @staticmethod
    def format_script_markdown(script: Script) -> str:
        lines = [
            f"# Roteiro do Vídeo — {script.project_id} (Versão {script.version})",
            "",
            f"- **Total de Cenas:** {script.total_scenes}",
            f"- **Duração Estimada Total:** {script.total_duration_seconds}s (~{round(script.total_duration_seconds / 60, 1)} min)",
            "",
            "---",
            "",
        ]
        for scene in script.scenes:
            lines.extend([
                f"## [{scene.scene_id}] {scene.title}",
                f"- **Duração:** {scene.duration_seconds}s",
                f"- **Objetivo:** {scene.objective}",
                f"- **Diretriz Visual:** {scene.visual_intent}",
                "",
                "### Narração:",
                f"> \"{scene.narration}\"",
                "",
                "---",
                "",
            ])
        return "\n".join(lines)

    @staticmethod
    def format_storyboard_markdown(storyboard: Storyboard) -> str:
        lines = [
            f"# Storyboard — {storyboard.project_id} (Versão {storyboard.version})",
            "",
            f"- **Total de Cenas:** {storyboard.total_scenes}",
            f"- **Duração Total:** {storyboard.total_duration_seconds}s",
            "",
            "| Cena | Duração | Tipo de Asset | Câmera | Transição | Descrição Visual |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for scene in storyboard.scenes:
            asset_type_val = scene.asset_type.value if hasattr(scene.asset_type, "value") else str(scene.asset_type)
            clean_desc = scene.visual_description.replace("\n", " ").replace("|", "-")
            lines.append(
                f"| `{scene.scene_id}` | {scene.duration_seconds}s | `{asset_type_val}` | {scene.camera} | {scene.transition} | {clean_desc} |"
            )

        lines.append("")
        lines.append("## Detalhamento Visual por Cena")
        lines.append("")
        for scene in storyboard.scenes:
            asset_type_val = scene.asset_type.value if hasattr(scene.asset_type, "value") else str(scene.asset_type)
            lines.extend([
                f"### Cena `{scene.scene_id}` ({scene.duration_seconds}s)",
                f"- **Narração de Apoio:** \"{scene.narration}\"",
                f"- **Tipo de Asset:** `{asset_type_val}`",
                f"- **Movimento de Câmera:** {scene.camera}",
                f"- **Transição:** {scene.transition}",
                f"- **Descrição Visual Detalhada:** {scene.visual_description}",
                "",
            ])
        return "\n".join(lines)
