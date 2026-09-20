"""
Worker runtime entrypoint for automated or pipeline execution.
Usage: python -m api.runtime.worker VIDEO_SPEC.yaml
"""
import sys
from pathlib import Path

# Force UTF-8 stream output if on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path if running directly
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api.agents.orchestrator.agent import VideoProductionAgent
from api.services.llm_service import LLMService


def main():
    if len(sys.argv) < 2:
        print("Uso: python -m api.runtime.worker <caminho_para_VIDEO_SPEC.yaml> [--mock]")
        sys.exit(1)

    spec_file = sys.argv[1]
    use_mock = "--mock" in sys.argv

    print(f"[*] Iniciando VideoProductionAgent para: {spec_file}")
    llm = LLMService(use_mock=use_mock)
    orchestrator = VideoProductionAgent(llm_service=llm)

    try:
        final_state = orchestrator.run(spec_file)
        print(f"[OK] Pipeline finalizado com sucesso!")
        print(f"    - ID do Projeto: {final_state.project_id}")
        print(f"    - Status Atual: {final_state.status.value}")
        print(f"    - Versão do Roteiro: v{final_state.versions.script}")
        print(f"    - Versão do Storyboard: v{final_state.versions.storyboard}")
        print(f"    - Roteiro JSON: {final_state.artifacts.script_json}")
        print(f"    - Storyboard JSON: {final_state.artifacts.storyboard_json}")
        print(f"\n[!] O projeto está em AWAITING_APPROVAL. Use o comando de aprovação ou revisão para prosseguir.")
    except Exception as e:
        print(f"[X] Erro na execução do pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
