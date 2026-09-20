"""
Domain models for VIDEO_SPEC — the single source of truth for video production.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ProjectMetadata(BaseModel):
    id: str = Field(..., min_length=1, description="Unique project identifier (slug)")
    title: str = Field(..., min_length=1, description="Human readable project title")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("project.id must only contain alphanumeric characters, hyphens or underscores")
        return v


class VideoDetails(BaseModel):
    objective: str = Field(..., min_length=5, description="Primary goal of the video")
    audience: str = Field(..., min_length=3, description="Target audience description")
    platform: str = Field(default="YouTube", description="Target publishing platform")
    language: str = Field(default="pt-BR", description="Language tag (e.g. pt-BR, en-US)")
    duration_seconds: int = Field(..., gt=0, description="Target total duration in seconds")
    aspect_ratio: str = Field(default="16:9", description="Video aspect ratio (e.g. 16:9, 9:16, 1:1)")


class StyleDetails(BaseModel):
    tone: str = Field(..., min_length=2, description="Tone of voice (e.g. educacional, dinâmico, corporativo)")
    visual_style: str = Field(default="moderno e didático", description="Visual aesthetic guidance")
    complexity: str = Field(default="iniciante", description="Technical depth (e.g. iniciante, intermediário, avançado)")


class ContentDetails(BaseModel):
    mandatory_topics: List[str] = Field(default_factory=list, description="List of topics that must be covered")


class ConstraintsDetails(BaseModel):
    avoid: List[str] = Field(default_factory=list, description="Things to avoid (e.g. jargões, claims sem comprovação)")


class VideoSpec(BaseModel):
    project: ProjectMetadata
    video: VideoDetails
    style: StyleDetails
    content: ContentDetails = Field(default_factory=ContentDetails)
    constraints: ConstraintsDetails = Field(default_factory=ConstraintsDetails)

    @classmethod
    def validate_raw_dict(cls, data: dict) -> tuple[bool, Optional[List[str]], Optional["VideoSpec"]]:
        """
        Validates raw dict data and returns (is_valid, missing_or_invalid_fields, video_spec_instance).
        """
        missing_fields = []
        project = data.get("project") or {}
        if not project.get("id"):
            missing_fields.append("project.id")
        if not project.get("title"):
            missing_fields.append("project.title")

        video = data.get("video") or {}
        if not video.get("objective"):
            missing_fields.append("video.objective")
        if not video.get("audience"):
            missing_fields.append("video.audience")
        if not video.get("language"):
            missing_fields.append("video.language")
        if not video.get("duration_seconds"):
            missing_fields.append("video.duration_seconds")

        style = data.get("style") or {}
        if not style.get("tone"):
            missing_fields.append("style.tone")

        if missing_fields:
            return False, missing_fields, None

        try:
            instance = cls.model_validate(data)
            return True, None, instance
        except Exception as e:
            return False, [str(e)], None
