"""
StoryboardAgent: Generates and revises structured storyboards based on Script.
"""
from pathlib import Path
from typing import Optional

from api.agents.base import BaseAgent
from api.domain.feedback import RevisionFeedback
from api.domain.script import Script
from api.domain.storyboard import AssetType, Storyboard, StoryboardScene
from api.services.llm_service import LLMService


class StoryboardAgent(BaseAgent):
    def __init__(self, llm_service: Optional[LLMService] = None, prompt_path: Optional[Path] = None):
        default_prompt = Path(__file__).resolve().parent.parent.parent / "prompts" / "storyboard_agent.md"
        super().__init__(llm_service=llm_service, prompt_path=prompt_path or default_prompt)

    def generate(
        self,
        script: Script,
        version: int = 1,
        previous_storyboard: Optional[Storyboard] = None,
        feedback: Optional[RevisionFeedback] = None,
    ) -> Storyboard:
        prompt_lines = [
            f"Gere um storyboard visual detalhado para o seguinte roteiro:",
            f"ID do Projeto: {script.project_id}",
            f"Versão do Roteiro: {script.version}",
            f"Total de Cenas: {script.total_scenes}",
            "",
            "Roteiro Completo:",
            script.model_dump_json(indent=2),
        ]

        if previous_storyboard and feedback:
            prompt_lines.extend([
                "",
                "---",
                "ATENÇÃO: ESTA É UMA REVISÃO DO STORYBOARD ANTERIOR.",
                f"Storyboard Anterior (Versão {previous_storyboard.version}):",
                previous_storyboard.model_dump_json(indent=2),
                "",
                f"INSTRUÇÃO DE FEEDBACK DO REVISOR HUMANO (DIREÇÃO VISUAL):",
                f"> \"{feedback.feedback}\"",
                "",
                "Ajuste as descrições visuais, câmera, transições e tipos de asset conforme solicitado.",
            ])

        user_prompt = "\n".join(prompt_lines)

        # Mock fallback for tests / offline
        mock_scenes = []
        for i, scene in enumerate(script.scenes):
            asset_type = AssetType.DIAGRAM if i % 2 == 0 else AssetType.ILLUSTRATION
            if feedback and "diagram" in feedback.feedback.lower():
                asset_type = AssetType.DIAGRAM

            mock_scenes.append(
                StoryboardScene(
                    scene_id=scene.scene_id,
                    duration_seconds=scene.duration_seconds,
                    narration=scene.narration,
                    visual_description=(
                        f"Plano visual de alta resolução representando {scene.visual_intent}."
                        if not feedback
                        else f"Plano visual revisado atendendo ao feedback: {feedback.feedback}. {scene.visual_intent}"
                    ),
                    camera="pan right" if i % 2 == 1 else "static",
                    transition="fade" if i > 0 else "cut",
                    asset_type=asset_type,
                )
            )

        mock_data = {
            "project_id": script.project_id,
            "version": version,
            "scenes": [s.model_dump() for s in mock_scenes],
        }

        result = self.llm_service.generate_structured(
            prompt=user_prompt,
            response_schema=Storyboard,
            system_instruction=self._system_prompt,
            mock_data=mock_data,
        )

        result.project_id = script.project_id
        result.version = version
        return result
