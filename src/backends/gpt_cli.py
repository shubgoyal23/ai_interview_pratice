"""
Backend: GPT via sgpt CLI (shell-gpt)
Requires: pip install shell-gpt  +  OPENAI_API_KEY env var
Docs: https://github.com/TheR1D/shell_gpt
"""

import subprocess
import uuid

from src.backends import AIBackend


class SGPTSession(AIBackend):
    def __init__(self, model: str = "gpt-4o"):
        self._model = model
        # Named chat session keeps conversation history across calls
        self._session = f"interview_{uuid.uuid4().hex[:8]}"

    def send(self, prompt: str) -> str:
        cmd = ["sgpt", "--model", self._model, "--chat", self._session, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout.strip()

    def close(self) -> None:
        pass
