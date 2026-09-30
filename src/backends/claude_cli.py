"""
Backend: Claude Code CLI (claude command)
Requires: Claude Code CLI installed and authenticated
Install: https://claude.ai/code
"""

import subprocess
import uuid

from src.backends import AIBackend


class ClaudeSession(AIBackend):
    def __init__(self, model: str = "default"):
        # "default" leaves model choice to the user's Claude Code settings.
        self._model = None if model == "default" else model
        self._session_id = str(uuid.uuid4())
        self._first = True

    def send(self, prompt: str) -> str:
        cmd = ["claude", "-p", prompt]
        if self._model:
            cmd += ["--model", self._model]
        if self._first:
            cmd += ["--session-id", self._session_id]
        else:
            cmd += ["--resume", self._session_id]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"claude CLI failed: {result.stderr.strip() or result.stdout.strip()}")
        self._first = False
        return result.stdout.strip()

    def close(self) -> None:
        pass
