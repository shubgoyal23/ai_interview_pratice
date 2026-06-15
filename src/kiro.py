import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import pexpect

_PROJECT_ROOT = Path(__file__).parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"

# Strips CSI, Fe, and OSC escape sequences
_ANSI = re.compile(
    r'\x1B(?:'
    r'[@-Z\\-_]'                       # Fe sequences
    r'|\[[0-?]*[ -/]*[@-~]'            # CSI sequences
    r'|\][^\x07\x1b]*(?:\x07|\x1b\\)' # OSC sequences
    r')'
)

# kiro streams responses by rewriting the current line with \r then new content.
# After stripping ANSI the full response sits between the last \r and end-of-chunk.
_CR_SPLIT = re.compile(r'\r(?!\n)')


def _parse_interactive(raw: str) -> str:
    """
    kiro rewrites its output line in-place using bare \r (no newline).
    The final rewrite is the complete response. We split on \r, strip ANSI from
    each segment, then take the last segment that contains '> '.
    """
    segments = _CR_SPLIT.split(raw)
    for seg in reversed(segments):
        clean = _ANSI.sub('', seg)
        # Skip input-prompt lines (kiro marks them with '% >')
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


class KiroSession:
    """Persistent kiro-cli process — one process per interview session."""

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
            maxread=65536,          # large buffer so long responses aren't split
            logfile=self._raw_log,  # every byte kiro writes goes here
            cwd=str(_PROJECT_ROOT),
        )
        # Drain startup output, wait until kiro is ready for first input
        self._child.expect(r'\?2004h', timeout=20)

    def send(self, prompt: str) -> str:
        self._child.send(f'\x1b[200~{prompt}\x1b[201~\r')
        # ▸ marks end of every response (credits line)
        self._child.expect('▸', timeout=120)
        response = _parse_interactive(self._child.before)
        # Wait for kiro to re-enable bracketed paste — only then is it ready
        # for the next message. Sending too early causes the input to be dropped.
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
