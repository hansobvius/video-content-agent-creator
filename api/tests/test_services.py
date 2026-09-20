import pytest
from pathlib import Path
import tempfile
import shutil

from api.domain.feedback import RevisionFeedback, RevisionTarget
from api.domain.project_state import ProjectStatus
from api.domain.script import Scene, Script
from api.domain.storyboard import AssetType, Storyboard, StoryboardScene
from api.domain.video_spec import VideoSpec
from api.services.approval_service import ApprovalService
from api.services.artifact_service import ArtifactService
from api.services.project_service import ProjectService
from api.services.state_service import StateService


@pytest.fixture
def temp_project_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def services(temp_project_dir):
    project_svc = ProjectService(base_dir=temp_project_dir)
    artifact_svc = ArtifactService(project_svc)
    state_svc = StateService(project_svc)
    approval_svc = ApprovalService(state_svc, artifact_svc)
    return project_svc, artifact_svc, state_svc, approval_svc


def test_artifact_versioning_and_persistence(services):
    project_svc, artifact_svc, state_svc, approval_svc = services
    project_id = "test-video"

    # 1. Save VideoSpec
    raw_data = {
        "project": {"id": project_id, "title": "Test Title"},
        "video": {
            "objective": "Explain AI",
            "audience": "Developers",
            "language": "pt-BR",
            "duration_seconds": 60,
        },
        "style": {"tone": "educacional"},
    }
    spec = VideoSpec.model_validate(raw_data)
    spec_path = artifact_svc.save_video_spec(project_id, spec)
    assert spec_path.exists()
    loaded_spec = artifact_svc.load_video_spec(project_id)
    assert loaded_spec.project.id == project_id

    # 2. Save Script v1
    scene1 = Scene(
        scene_id="scene_001",
        title="Intro",
        duration_seconds=10,
        narration="Narration 1",
        objective="Obj 1",
        visual_intent="Intent 1",
    )
    script_v1 = Script(project_id=project_id, version=1, scenes=[scene1])
    j1, m1 = artifact_svc.save_script(script_v1)
    assert j1.exists() and m1.exists()

    # 3. Save Script v2 (must not overwrite v1)
    script_v2 = Script(project_id=project_id, version=2, scenes=[scene1])
    j2, m2 = artifact_svc.save_script(script_v2)
    assert j2.exists() and j1.exists()
    assert j2.name == "script_v2.json"
    assert j1.name == "script_v1.json"

    # 4. Save Storyboard v1 and v2
    s_scene = StoryboardScene(
        scene_id="scene_001",
        duration_seconds=10,
        narration="Narration 1",
        visual_description="Visual 1",
        camera="static",
        transition="cut",
        asset_type=AssetType.ILLUSTRATION,
    )
    sb_v1 = Storyboard(project_id=project_id, version=1, scenes=[s_scene])
    sb_j1, _ = artifact_svc.save_storyboard(sb_v1)
    assert sb_j1.exists()

    sb_v2 = Storyboard(project_id=project_id, version=2, scenes=[s_scene])
    sb_j2, _ = artifact_svc.save_storyboard(sb_v2)
    assert sb_j2.exists() and sb_j1.exists()


def test_state_service_and_approval_workflow(services):
    project_svc, artifact_svc, state_svc, approval_svc = services
    project_id = "approval-proj"

    # Init state
    state = state_svc.init_state(project_id)
    assert state.status == ProjectStatus.CREATED

    # Move to AWAITING_APPROVAL
    state = state_svc.transition(project_id, ProjectStatus.AWAITING_APPROVAL)
    assert state.status == ProjectStatus.AWAITING_APPROVAL

    # Request revision with target 'storyboard'
    feedback_record = approval_svc.request_revision(
        project_id=project_id,
        target=RevisionTarget.STORYBOARD,
        feedback_text="Change visual framing",
    )
    assert feedback_record.revision_number == 1
    state = state_svc.get_state(project_id)
    assert state.status == ProjectStatus.REVISION_STORYBOARD_REQUESTED
    assert state.versions.revision == 1

    # Transition back to AWAITING_APPROVAL and then approve
    state_svc.transition(project_id, ProjectStatus.AWAITING_APPROVAL)
    result = approval_svc.approve(project_id)
    assert result["status"] == "APPROVED"
    assert state_svc.get_state(project_id).status == ProjectStatus.APPROVED
