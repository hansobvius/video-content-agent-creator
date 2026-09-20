"""
Domain models for Storyboard and visual scene planning.
"""
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    ILLUSTRATION = "illustration"
    IMAGE = "image"
    VIDEO = "video"
    DIAGRAM = "diagram"
    TEXT_ANIMATION = "text_animation"
    STOCK = "stock"


class StoryboardScene(BaseModel):
    scene_id: str = Field(..., description="Matching scene_id from script")
    duration_seconds: int = Field(..., gt=0, description="Duration in seconds")
    narration: str = Field(..., description="Spoken narration for context")
    visual_description: str = Field(..., description="Detailed visual prompt / scene description for generation")
    camera: str = Field(default="static", description="Camera movement or framing (e.g. static, pan right, close-up)")
    transition: str = Field(default="fade", description="Transition to next scene (e.g. cut, fade, slide)")
    asset_type: AssetType = Field(default=AssetType.ILLUSTRATION, description="Expected visual asset type")


class Storyboard(BaseModel):
    project_id: str = Field(..., description="Associated project ID")
    version: int = Field(default=1, ge=1, description="Storyboard version number")
    scenes: List[StoryboardScene] = Field(..., min_length=1, description="Ordered storyboard scenes")

    @property
    def total_duration_seconds(self) -> int:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def total_scenes(self) -> int:
        return len(self.scenes)
