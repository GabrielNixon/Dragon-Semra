"""Helpers for optional LLM-backed synonym generation."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import List, Optional


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM client cannot be configured correctly."""


@dataclass
class LLMSynonymClient:
    """Simple HTTP client that calls a chat-completions style API."""

    provider: str
    model: str
    max_synonyms: int = 5
    prompt_template: Optional[str] = None
    system_prompt: Optional[str] = None
    timeout: int = 30

    def __post_init__(self) -> None:
        self.provider = self.provider.lower()
        self.api_key = os.getenv("DRAGON_SEMRA_LLM_KEY")
        if not self.api_key:
            raise LLMConfigurationError(
                "Environment variable DRAGON_SEMRA_LLM_KEY must be set to use the LLM." 
            )
        self.prompt_template = (
            self.prompt_template
            or (
                "Generate up to {max_synonyms} synonyms, abbreviations, or shorthand labels for the term "
                '"{term}". {context_instruction}Respond with a comma-separated list.'
            )
        )
        self.system_prompt = self.system_prompt or (
            "You are a biomedical terminology assistant that suggests concise synonyms."
        )

    def generate_synonyms(self, term: str, *, context: str | None = None) -> List[str]:
        if self.provider != "openai":
            raise LLMConfigurationError(f"Unsupported LLM provider: {self.provider}")
        return self._call_openai(term, context=context)

    def _call_openai(self, term: str, *, context: str | None = None) -> List[str]:
        context_instruction = ""
        if context:
            context_instruction = f"Context:\n{context}\n"

        prompt = self.prompt_template.format(
            term=term,
            max_synonyms=self.max_synonyms,
            context_instruction=context_instruction,
        )

        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:  # pragma: no cover - network interaction
            raise RuntimeError(f"Failed to contact OpenAI API: {exc}") from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - depends on API response
            raise RuntimeError(f"Unexpected OpenAI response: {payload}") from exc

        return _parse_synonym_list(content)


def _parse_synonym_list(content: str) -> List[str]:
    # Allow comma, semicolon, or newline separated content
    tokens = re.split(r"[,;\n]+", content)
    return [token.strip() for token in tokens if token.strip()]


__all__ = ["LLMSynonymClient", "LLMConfigurationError"]

