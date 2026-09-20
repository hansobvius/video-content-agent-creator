"""
Domain models for Script and Scenes.
"""
from typing import List
from pydantic import BaseModel, Field


class Scene(BaseModel):
    scene_id: str = Field(..., description="Unique scene identifier, e.g. scene_001")
    title: str = Field(..., description="Short scene title or section name")
    duration_seconds: int = Field(..., gt=0, description="Estimated duration of this scene in seconds")
    narration: str = Field(..., description="Voiceover or spoken narration script")
    objective: str = Field(..., description="Purpose or goal of this scene")
    visual_intent: str = Field(..., description="High-level visual direction for this scene")


class Script(BaseModel):
    project_id: str = Field(..., description="Associated project ID")
    version: int = Field(default=1, ge=1, description="Script version number")
    scenes: List[Scene] = Field(..., min_length=1, description="Ordered list of scenes in the script")

    @property
    def total_duration_seconds(self) -> int:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def total_scenes(self) -> int:
        return len(self.scenes)
