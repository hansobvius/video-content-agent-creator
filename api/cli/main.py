"""
CLI interface for the Video Content Agent Creator platform.
"""
from pathlib import Path
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

# Force UTF-8 stream output if on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from api.agents.orchestrator.agent import VideoProductionAgent
from api.domain.feedback import RevisionTarget
from api.domain.project_state import ProjectStatus
from api.services.approval_service import ApprovalService
from api.services.artifact_service import ArtifactService
from api.services.llm_service import LLMService
from api.services.project_service import ProjectService
from api.services.state_service import StateService

app = typer.Typer(
    name="video-agent",
    help="CLI para automação da produção de roteiros e storyboards com agentes de IA.",
    add_completion=False,
)
console = Console(safe_box=True)


@app.command()
def run(
    spec_path: str = typer.Argument(..., help="Caminho para o arquivo VIDEO_SPEC.yaml"),
    mock: bool = typer.Option(False, "--mock", help="Executar em modo offline/mock sem consumir API de LLM"),
):
    """
    Inicia o fluxo de produção de vídeo a partir de uma especificação VIDEO_SPEC.yaml.
    """
    path = Path(spec_path)
    if not path.exists():
        console.print(f"[bold red]Erro:[/bold red] Arquivo '{spec_path}' não encontrado.")
        raise typer.Exit(code=1)

    console.print(Panel.fit(f"[bold cyan]Iniciando Orquestrador de Produção Audiovisual[/bold cyan]\nEspecificação: {spec_path} | Modo Mock: {mock}", border_style="cyan"))

    llm = LLMService(use_mock=mock)
    orchestrator = VideoProductionAgent(llm_service=llm)

    try:
        state = orchestrator.run(path)
        console.print("\n[bold green][OK] Pipeline inicial executado com sucesso![/bold green]")
        _display_state_summary(state)
        console.print("\n[yellow]Projeto aguardando revisão humana (AWAITING_APPROVAL).[/yellow]")
        console.print("Comandos úteis:")
        console.print(f"  - Ver status:   [cyan]python -m api.cli.main status {state.project_id}[/cyan]")
        console.print(f"  - Ver roteiro:  [cyan]python -m api.cli.main show {state.project_id} --type script[/cyan]")
        console.print(f"  - Ver storyboard: [cyan]python -m api.cli.main show {state.project_id} --type storyboard[/cyan]")
        console.print(f"  - Aprovar:      [cyan]python -m api.cli.main approve {state.project_id}[/cyan]")
        console.print(f"  - Revisar:      [cyan]python -m api.cli.main revise {state.project_id} --target storyboard --feedback 'Ajustar cena 2'[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Erro durante a execução:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def status(
    project_id: str = typer.Argument(..., help="ID do projeto"),
):
    """
    Exibe o status atual, versões de artefatos e histórico de um projeto.
    """
    state_service = StateService()
    try:
        state = state_service.get_state(project_id)
        _display_state_summary(state)
    except FileNotFoundError:
        console.print(f"[bold red]Erro:[/bold red] Projeto '{project_id}' não encontrado.")
        raise typer.Exit(code=1)


@app.command()
def show(
    project_id: str = typer.Argument(..., help="ID do projeto"),
    type: str = typer.Option("script", "--type", "-t", help="Tipo de artefato: 'script' ou 'storyboard'"),
    version: Optional[int] = typer.Option(None, "--version", "-v", help="Número da versão específica"),
):
    """
    Renderiza no terminal o conteúdo formatado do Roteiro ou Storyboard.
    """
    state_service = StateService()
    artifact_service = ArtifactService()

    try:
        state = state_service.get_state(project_id)
    except FileNotFoundError:
        console.print(f"[bold red]Erro:[/bold red] Projeto '{project_id}' não encontrado.")
        raise typer.Exit(code=1)

    type_lower = type.lower()
    if type_lower == "script":
        target_version = version or state.versions.script
        if target_version == 0:
            console.print("[yellow]Nenhum roteiro gerado ainda.[/yellow]")
            return
        script = artifact_service.load_script(project_id, target_version)
        md_text = artifact_service.format_script_markdown(script)
        console.print(Markdown(md_text))

    elif type_lower == "storyboard":
        target_version = version or state.versions.storyboard
        if target_version == 0:
            console.print("[yellow]Nenhum storyboard gerado ainda.[/yellow]")
            return
        storyboard = artifact_service.load_storyboard(project_id, target_version)
        md_text = artifact_service.format_storyboard_markdown(storyboard)
        console.print(Markdown(md_text))

    else:
        console.print("[bold red]Erro:[/bold red] Tipo inválido. Use 'script' ou 'storyboard'.")


@app.command()
def approve(
    project_id: str = typer.Argument(..., help="ID do projeto a ser aprovado"),
):
    """
    Aprova o plano de produção (Human-in-the-Loop Approval).
    """
    approval_service = ApprovalService()
    try:
        result = approval_service.approve(project_id)
        console.print(f"[bold green][OK] {result['message']}[/bold green] (Status: [bold]{result['status']}[/bold])")
    except Exception as e:
        console.print(f"[bold red]Erro ao aprovar:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def revise(
    project_id: str = typer.Argument(..., help="ID do projeto a ser revisado"),
    target: str = typer.Option(..., "--target", "-t", help="Alvo da revisão: 'script' ou 'storyboard'"),
    feedback: str = typer.Option(..., "--feedback", "-f", help="Instruções de feedback para o agente"),
    mock: bool = typer.Option(False, "--mock", help="Executar em modo mock/offline"),
):
    """
    Solicita revisão granular de roteiro ou storyboard.
    """
    target_clean = target.strip().lower()
    if target_clean not in ("script", "storyboard"):
        console.print("[bold red]Erro:[/bold red] --target deve ser 'script' ou 'storyboard'.")
        raise typer.Exit(code=1)

    revision_target = RevisionTarget.SCRIPT if target_clean == "script" else RevisionTarget.STORYBOARD

    console.print(Panel.fit(
        f"[bold yellow]Solicitando Revisão Granular[/bold yellow]\n"
        f"Projeto: {project_id}\n"
        f"Alvo: {revision_target.value.upper()}\n"
        f"Instrução: \"{feedback}\"",
        border_style="yellow",
    ))

    llm = LLMService(use_mock=mock)
    orchestrator = VideoProductionAgent(llm_service=llm)

    try:
        final_state = orchestrator.process_revision(
            project_id=project_id,
            target=revision_target,
            feedback_text=feedback,
        )
        console.print("\n[bold green][OK] Revisão processada com sucesso![/bold green]")
        _display_state_summary(final_state)
    except Exception as e:
        console.print(f"[bold red]Erro durante o processamento da revisão:[/bold red] {e}")
        raise typer.Exit(code=1)


def _display_state_summary(state):
    table = Table(title=f"Estado do Projeto: {state.project_id}", show_header=True, header_style="bold magenta")
    table.add_column("Propriedade", style="cyan", width=25)
    table.add_column("Valor", style="white")

    status_color = "green" if state.status == ProjectStatus.APPROVED else "yellow" if state.status == ProjectStatus.AWAITING_APPROVAL else "red" if state.status == ProjectStatus.FAILED else "cyan"

    table.add_row("Status", f"[{status_color}]{state.status.value}[/{status_color}]")
    table.add_row("Etapa Atual", state.current_stage)
    table.add_row("Versão Roteiro", f"v{state.versions.script}")
    table.add_row("Versão Storyboard", f"v{state.versions.storyboard}")
    table.add_row("Revisões Registradas", str(state.versions.revision))
    table.add_row("Última Atualização", state.updated_at)
    if state.artifacts.script_json:
        table.add_row("Roteiro JSON", state.artifacts.script_json)
    if state.artifacts.storyboard_json:
        table.add_row("Storyboard JSON", state.artifacts.storyboard_json)
    if state.artifacts.last_feedback:
        table.add_row("Último Feedback", state.artifacts.last_feedback)

    console.print(table)


if __name__ == "__main__":
    app()
