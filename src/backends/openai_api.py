"""
Backend: OpenAI API
Requires: OPENAI_API_KEY env var  (or pass api_key= directly)
Models:   gpt-4o, gpt-4o-mini, gpt-4-turbo, o1, o3-mini …
"""

import os

from openai import OpenAI

from src.backends import AIBackend


class OpenAISession(AIBackend):
    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
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

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": self._system}] + self._messages,
        )
        content = response.choices[0].message.content or ""
        self._messages.append({"role": "assistant", "content": content})
        return content

    def close(self) -> None:
        self._messages.clear()
