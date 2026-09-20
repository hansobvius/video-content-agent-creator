"""
ScriptAgent: Generates and revises structured video scripts based on VideoSpec.
"""
from pathlib import Path
from typing import Optional

from api.agents.base import BaseAgent
from api.domain.feedback import RevisionFeedback
from api.domain.script import Scene, Script
from api.domain.video_spec import VideoSpec
from api.services.llm_service import LLMService


class ScriptAgent(BaseAgent):
    def __init__(self, llm_service: Optional[LLMService] = None, prompt_path: Optional[Path] = None):
        default_prompt = Path(__file__).resolve().parent.parent.parent / "prompts" / "script_agent.md"
        super().__init__(llm_service=llm_service, prompt_path=prompt_path or default_prompt)

    def generate(
        self,
        spec: VideoSpec,
        version: int = 1,
        previous_script: Optional[Script] = None,
        feedback: Optional[RevisionFeedback] = None,
    ) -> Script:
        prompt_lines = [
            f"Gere um roteiro completo e estruturado para o seguinte projeto:",
            f"ID do Projeto: {spec.project.id}",
            f"Título: {spec.project.title}",
            f"Objetivo: {spec.video.objective}",
            f"Público-alvo: {spec.video.audience}",
            f"Idioma: {spec.video.language}",
            f"Duração Total Alvo: {spec.video.duration_seconds} segundos",
            f"Tom: {spec.style.tone}",
            f"Estilo Visual: {spec.style.visual_style}",
            f"Complexidade: {spec.style.complexity}",
            f"Tópicos Obrigatórios: {', '.join(spec.content.mandatory_topics) if spec.content.mandatory_topics else 'Nenhum'}",
            f"Evitar: {', '.join(spec.constraints.avoid) if spec.constraints.avoid else 'Nenhum'}",
        ]

        if previous_script and feedback:
            prompt_lines.extend([
                "",
                "---",
                "ATENÇÃO: ESTA É UMA REVISÃO DO ROTEIRO ANTERIOR.",
                f"Roteiro Anterior (Versão {previous_script.version}):",
                previous_script.model_dump_json(indent=2),
                "",
                f"INSTRUÇÃO DE FEEDBACK DO REVISOR HUMANO:",
                f"> \"{feedback.feedback}\"",
                "",
                "Aplique as correções solicitadas mantendo a coesão geral e respeitando a duração alvo.",
            ])

        user_prompt = "\n".join(prompt_lines)

        # Mock fallback for offline or tests
        mock_scenes = [
            Scene(
                scene_id="scene_001",
                title="Introdução",
                duration_seconds=int(spec.video.duration_seconds * 0.15) or 15,
                narration=f"Olá! Hoje vamos entender tudo sobre {spec.project.title}.",
                objective="Apresentar o tema e prender a atenção do espectador.",
                visual_intent=f"Veículo em destaque com gráficos modernos e estilo {spec.style.visual_style}.",
            ),
            Scene(
                scene_id="scene_002",
                title="Conceito Principal",
                duration_seconds=int(spec.video.duration_seconds * 0.35) or 45,
                narration=(
                    f"Para entendermos o funcionamento, veja como os principais componentes interagem de forma integrada."
                    if not feedback
                    else f"Explicando de forma simples e direta: os componentes principais interagem com alta eficiência."
                ),
                objective="Explicar a dinâmica central do conteúdo.",
                visual_intent="Animação esquemática mostrando fluxo de energia e peças centrais.",
            ),
            Scene(
                scene_id="scene_003",
                title="Aprofundamento dos Tópicos",
                duration_seconds=int(spec.video.duration_seconds * 0.35) or 45,
                narration=(
                    f"Cobrimos tópicos essenciais como {', '.join(spec.content.mandatory_topics[:3]) if spec.content.mandatory_topics else 'os modos de operação'}."
                ),
                objective="Detalhar os tópicos obrigatórios do briefing.",
                visual_intent="Cortes alternados com elementos visuais elucidativos.",
            ),
            Scene(
                scene_id="scene_004",
                title="Conclusão e Encerramento",
                duration_seconds=int(spec.video.duration_seconds * 0.15) or 15,
                narration=f"Agora você conhece como funciona {spec.project.title}. Deixe seu like e até a próxima!",
                objective="Resumir os pontos-chave e convidar à ação.",
                visual_intent="Resumo visual com call to action final.",
            ),
        ]

        mock_data = {
            "project_id": spec.project.id,
            "version": version,
            "scenes": [s.model_dump() for s in mock_scenes],
        }

        result = self.llm_service.generate_structured(
            prompt=user_prompt,
            response_schema=Script,
            system_instruction=self._system_prompt,
            mock_data=mock_data,
        )

        result.project_id = spec.project.id
        result.version = version
        return result
