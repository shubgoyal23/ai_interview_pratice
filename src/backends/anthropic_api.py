"""
Backend: Anthropic API (Claude)
Requires: ANTHROPIC_API_KEY env var  (or pass api_key= directly)
Models:   claude-sonnet-4-6, claude-opus-4-8, claude-haiku-4-5 …
"""

import os

import anthropic

from src.backends import AIBackend


class AnthropicSession(AIBackend):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._model = model
        self._messages: list[dict] = []
        self._system: str | None = None

    def send(self, prompt: str) -> str:
        if self._system is None:
            self._system = prompt
            user_msg = "Begin the interview."
        else:
            user_msg = prompt

        self._messages.append({"role": "user", "content": user_msg})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=self._system,
            messages=self._messages,
        )
        content = response.content[0].text
        self._messages.append({"role": "assistant", "content": content})
        return content

    def close(self) -> None:
        self._messages.clear()
