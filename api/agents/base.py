"""
Base class for LLM-powered agents.
"""
from pathlib import Path
from typing import Optional

from api.services.llm_service import LLMService


class BaseAgent:
    def __init__(self, llm_service: Optional[LLMService] = None, prompt_path: Optional[Path] = None):
        self.llm_service = llm_service or LLMService()
        self.prompt_path = prompt_path
        self._system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        if self.prompt_path and self.prompt_path.exists():
            return self.prompt_path.read_text(encoding="utf-8")
        return ""
