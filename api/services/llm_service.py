"""
LLM Service abstraction with support for Structured Outputs (Gemini) and Mock Provider for tests.
"""
import json
import os
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class LLMService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        use_mock: bool = False,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.use_mock = use_mock or (not bool(self.api_key))
        self._client = None

        if not self.use_mock and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                # If google-genai is not available or fails to initialize, fallback to mock mode if configured
                self.use_mock = True

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        mock_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> T:
        """
        Generates a structured Pydantic object from the LLM, validating schema with retries.
        """
        if self.use_mock:
            if mock_data is not None:
                return response_schema.model_validate(mock_data)
            raise ValueError("LLMService is in mock mode but no mock_data was provided.")

        last_error = None
        current_prompt = prompt

        for attempt in range(max_retries + 1):
            try:
                # Use Google GenAI SDK structured output
                config: Dict[str, Any] = {
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                }
                if system_instruction:
                    config["system_instruction"] = system_instruction

                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=current_prompt,
                    config=config,
                )

                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                parsed_json = json.loads(response_text)
                return response_schema.model_validate(parsed_json)
            except Exception as e:
                last_error = e
                current_prompt = (
                    f"{prompt}\n\n[IMPORTANTE] A tentativa anterior falhou com o erro: {str(e)}.\n"
                    f"Certifique-se de responder RIGOROSAMENTE de acordo com o formato JSON esperado."
                )

        raise RuntimeError(f"Failed to generate valid structured output after {max_retries + 1} attempts: {last_error}")
