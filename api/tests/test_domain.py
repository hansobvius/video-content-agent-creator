import pytest
from api.domain.video_spec import VideoSpec
from api.domain.script import Script, Scene
from api.domain.storyboard import Storyboard, StoryboardScene, AssetType
from api.domain.project_state import ProjectState, ProjectStatus
from api.domain.feedback import RevisionFeedback, RevisionTarget


def test_video_spec_validation_success():
    raw_data = {
        "project": {"id": "test-video", "title": "Test Video"},
        "video": {
            "objective": "Explain AI Agents",
            "audience": "Developers",
            "language": "pt-BR",
            "duration_seconds": 120,
            "aspect_ratio": "16:9",
        },
        "style": {"tone": "educacional", "visual_style": "moderno"},
        "content": {"mandatory_topics": ["topic1", "topic2"]},
        "constraints": {"avoid": ["jargon"]},
    }
    is_valid, errors, spec = VideoSpec.validate_raw_dict(raw_data)
    assert is_valid is True
    assert errors is None
    assert spec is not None
    assert spec.project.id == "test-video"
    assert spec.video.duration_seconds == 120


def test_video_spec_missing_fields():
    raw_data = {
        "project": {"id": "test-video"},  # Missing title
        "video": {"objective": "Explain AI Agents"},  # Missing audience, duration_seconds, etc.
    }
    is_valid, errors, spec = VideoSpec.validate_raw_dict(raw_data)
    assert is_valid is False
    assert spec is None
    assert "project.title" in errors
    assert "video.audience" in errors
    assert "video.duration_seconds" in errors
    assert "style.tone" in errors


def test_script_model():
    scene1 = Scene(
        scene_id="scene_001",
        title="Intro",
        duration_seconds=10,
        narration="Hello world",
        objective="Introduce topic",
        visual_intent="Showing logo",
    )
    scene2 = Scene(
        scene_id="scene_002",
        title="Body",
        duration_seconds=30,
        narration="Explanation",
        objective="Explain concept",
        visual_intent="Diagram animation",
    )
    script = Script(project_id="test-proj", version=1, scenes=[scene1, scene2])
    assert script.total_scenes == 2
    assert script.total_duration_seconds == 40


def test_storyboard_model():
    scene = StoryboardScene(
        scene_id="scene_001",
        duration_seconds=15,
        narration="Test narration",
        visual_description="Detailed visual prompt",
        camera="pan right",
        transition="fade",
        asset_type=AssetType.DIAGRAM,
    )
    storyboard = Storyboard(project_id="test-proj", version=1, scenes=[scene])
    assert storyboard.total_scenes == 1
    assert storyboard.total_duration_seconds == 15
    assert storyboard.scenes[0].asset_type == AssetType.DIAGRAM


def test_project_state_transitions():
    state = ProjectState(project_id="test-proj")
    assert state.status == ProjectStatus.CREATED
    assert len(state.history) == 0

    state.transition_to(ProjectStatus.SPEC_VALIDATED, stage="spec_validated")
    assert state.status == ProjectStatus.SPEC_VALIDATED
    assert len(state.history) == 1
    assert state.history[0].to_status == ProjectStatus.SPEC_VALIDATED


def test_revision_feedback():
    fb = RevisionFeedback(
        project_id="test-proj",
        revision_number=1,
        target=RevisionTarget.STORYBOARD,
        feedback="Adjust visual framing in scene 2",
    )
    assert fb.target == RevisionTarget.STORYBOARD
    assert fb.revision_number == 1
