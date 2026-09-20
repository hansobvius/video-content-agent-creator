import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from api.agents.orchestrator.agent import VideoProductionAgent
from api.domain.feedback import RevisionTarget
from api.domain.project_state import ProjectStatus
from api.services.llm_service import LLMService
from api.services.project_service import ProjectService


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_spec_file(temp_workspace):
    spec_data = {
        "project": {
            "id": "test-orchestrator-video",
            "title": "Vídeo de Teste Completo",
        },
        "video": {
            "objective": "Demonstrar o fluxo completo de agentes",
            "audience": "Engenheiros de Software",
            "language": "pt-BR",
            "duration_seconds": 180,
            "aspect_ratio": "16:9",
        },
        "style": {
            "tone": "educacional",
            "visual_style": "minimalista",
            "complexity": "iniciante",
        },
        "content": {
            "mandatory_topics": ["intro", "agentes", "conclusao"],
        },
        "constraints": {
            "avoid": ["erros conceituais"],
        },
    }
    spec_path = temp_workspace / "VIDEO_SPEC.yaml"
    with open(spec_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(spec_data, f)
    return spec_path


def test_full_orchestrator_pipeline_and_granular_revisions(temp_workspace, sample_spec_file):
    project_svc = ProjectService(base_dir=temp_workspace / "projects")
    llm = LLMService(use_mock=True)
    orchestrator = VideoProductionAgent(
        project_service=project_svc,
        llm_service=llm,
    )

    # 1. Initial Run
    state = orchestrator.run(sample_spec_file)
    assert state.project_id == "test-orchestrator-video"
    assert state.status == ProjectStatus.AWAITING_APPROVAL
    assert state.versions.script == 1
    assert state.versions.storyboard == 1

    # Verify files exist on disk
    scripts_dir = project_svc.get_scripts_dir(state.project_id)
    storyboards_dir = project_svc.get_storyboards_dir(state.project_id)
    logs_dir = project_svc.get_logs_dir(state.project_id)

    assert (scripts_dir / "script_v1.json").exists()
    assert (scripts_dir / "script_v1.md").exists()
    assert (storyboards_dir / "storyboard_v1.json").exists()
    assert (storyboards_dir / "storyboard_v1.md").exists()
    assert (logs_dir / "execution.log").exists()

    # 2. Granular Revision: Storyboard Only
    revised_sb_state = orchestrator.process_revision(
        project_id=state.project_id,
        target=RevisionTarget.STORYBOARD,
        feedback_text="Mude o estilo visual da cena 2 para diagram",
    )
    assert revised_sb_state.status == ProjectStatus.AWAITING_APPROVAL
    assert revised_sb_state.versions.script == 1  # Script was untouched!
    assert revised_sb_state.versions.storyboard == 2  # Storyboard bumped to v2
    assert (storyboards_dir / "storyboard_v2.json").exists()

    # 3. Granular Revision: Script
    revised_sc_state = orchestrator.process_revision(
        project_id=state.project_id,
        target=RevisionTarget.SCRIPT,
        feedback_text="Simplifique a explicação na introdução",
    )
    assert revised_sc_state.status == ProjectStatus.AWAITING_APPROVAL
    assert revised_sc_state.versions.script == 2  # Script bumped to v2
    assert revised_sc_state.versions.storyboard == 3  # Storyboard regenerated for script v2
    assert (scripts_dir / "script_v2.json").exists()
    assert (storyboards_dir / "storyboard_v3.json").exists()

    # 4. Final Approval
    approval_res = orchestrator.approval_service.approve(state.project_id)
    assert approval_res["status"] == "APPROVED"
    final_state = orchestrator.state_service.get_state(state.project_id)
    assert final_state.status == ProjectStatus.APPROVED
