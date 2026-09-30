"""
Backend: Kiro CLI (persistent PTY session via pexpect)
Requires: kiro-cli installed and logged in
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import pexpect

from src.backends import AIBackend

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"

_ANSI = re.compile(
    r'\x1B(?:'
    r'[@-Z\\-_]'
    r'|\[[0-?]*[ -/]*[@-~]'
    r'|\][^\x07\x1b]*(?:\x07|\x1b\\)'
    r')'
)
_CR_SPLIT = re.compile(r'\r(?!\n)')


def _parse(raw: str) -> str:
    for seg in reversed(_CR_SPLIT.split(raw)):
        clean = _ANSI.sub('', seg)
        if '% >' in clean:
            continue
        if '> ' in clean:
            idx = clean.rfind('> ')
            text = clean[idx + 2:].strip()
            if text:
                return text
    return ''


def get_latest_session_id() -> str | None:
    result = subprocess.run(
        ['kiro-cli', 'chat', '--list-sessions', '--format', 'json'],
        capture_output=True, text=True, cwd=str(_PROJECT_ROOT),
    )
    try:
        data = json.loads(_ANSI.sub('', result.stdout))
        return data[0]['sessions'][0]['sessionId']
    except (json.JSONDecodeError, IndexError, KeyError):
        return None


class KiroSession(AIBackend):
    def __init__(self, model: str, session_id: str | None = None):
        _LOG_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._raw_log = (_LOG_DIR / f"kiro_raw_{ts}.log").open('w', buffering=1)

        args = ['chat', '--classic', '--model', model]
        if session_id:
            args += ['--resume-id', session_id]

        self._child = pexpect.spawn(
            'kiro-cli', args,
            encoding='utf-8',
            timeout=120,
            maxread=65536,
            logfile=self._raw_log,
            cwd=str(_PROJECT_ROOT),
        )
        self._child.expect(r'\?2004h', timeout=20)

    def send(self, prompt: str) -> str:
        self._child.send(f'\x1b[200~{prompt}\x1b[201~\r')
        self._child.expect('▸', timeout=120)
        response = _parse(self._child.before)
        try:
            self._child.expect(r'\?2004h', timeout=15)
        except pexpect.TIMEOUT:
            pass
        return response

    def close(self) -> None:
        try:
            self._child.close(force=True)
        except Exception:
            pass
        try:
            self._raw_log.close()
        except Exception:
            pass
