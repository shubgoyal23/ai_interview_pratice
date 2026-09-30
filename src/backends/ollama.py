"""
Backend: Ollama (local open-source models)
Requires: Ollama running locally — https://ollama.com
          ollama pull llama3.1   (or whichever model you choose)
Models:   llama3.1, mistral, gemma2, phi3, qwen2, deepseek-r1 …
"""

import requests

from src.backends import AIBackend

_BASE_URL = "http://localhost:11434"


class OllamaSession(AIBackend):
    def __init__(self, model: str = "llama3.1"):
        self._model = model
        self._messages: list[dict] = []
        self._system: str | None = None

    def send(self, prompt: str) -> str:
        if self._system is None:
            # First call: treat prompt as system instructions, kick off with a starter
            self._system = prompt
            user_msg = "Begin the interview."
        else:
            user_msg = prompt

        self._messages.append({"role": "user", "content": user_msg})

        resp = requests.post(
            f"{_BASE_URL}/api/chat",
            json={
                "model": self._model,
                "messages": [{"role": "system", "content": self._system}] + self._messages,
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        self._messages.append({"role": "assistant", "content": content})
        return content

    def close(self) -> None:
        self._messages.clear()
