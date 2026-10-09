"""
Backend: Claude Code CLI (claude command)
Requires: Claude Code CLI installed and authenticated
Install: https://claude.ai/code
"""

import subprocess
import uuid
from pathlib import Path

from src.backends import AIBackend

# Claude stores sessions per directory; always run from the project root so resume works
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ClaudeSession(AIBackend):
    def __init__(self, model: str = "default", session_id: str | None = None):
        # "default" leaves model choice to the user's Claude Code settings.
        self._model = None if model == "default" else model
        # Resuming an existing session skips creating a new one
        self.session_id = session_id or str(uuid.uuid4())
        self._first = session_id is None

    def send(self, prompt: str) -> str:
        cmd = ["claude", "-p", prompt]
        if self._model:
            cmd += ["--model", self._model]
        if self._first:
            cmd += ["--session-id", self.session_id]
        else:
            cmd += ["--resume", self.session_id]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=_PROJECT_ROOT)
        if result.returncode != 0:
            raise RuntimeError(f"claude CLI failed: {result.stderr.strip() or result.stdout.strip()}")
        self._first = False
        return result.stdout.strip()

    def close(self) -> None:
        pass
