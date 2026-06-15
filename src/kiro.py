import json
import re
import subprocess
import sys
from pathlib import Path

_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

_PROJECT_ROOT = Path(__file__).parent.parent


def _parse_response(raw: str) -> str:
    clean = _ANSI.sub('', raw)
    response_lines = []
    capturing = False
    for line in clean.splitlines():
        if line.startswith('> '):
            capturing = True
            response_lines.append(line[2:])
        elif capturing:
            if '▸' in line or line.strip().startswith('Credits'):
                break
            if line.strip():
                response_lines.append(line)
    return '\n'.join(response_lines).strip()


def get_latest_session_id() -> str | None:
    result = subprocess.run(
        ["kiro-cli", "chat", "--list-sessions", "--format", "json"],
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )
    try:
        data = json.loads(_ANSI.sub('', result.stdout))
        return data[0]["sessions"][0]["sessionId"]
    except (json.JSONDecodeError, IndexError, KeyError):
        return None


def query_kiro(prompt: str, model: str, session_id: str | None = None) -> str:
    cmd = ["kiro-cli", "chat", prompt, "--no-interactive", "--model", model]
    if session_id:
        cmd += ["--resume-id", session_id]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_PROJECT_ROOT),
    )
    if result.returncode != 0:
        print(f"[kiro-cli error]: {_ANSI.sub('', result.stderr).strip()}", file=sys.stderr)
    return _parse_response(result.stdout)
