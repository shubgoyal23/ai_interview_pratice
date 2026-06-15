import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _load() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text())
    return {}


def _save(data: dict) -> None:
    _CONFIG_PATH.write_text(json.dumps(data, indent=2))


def get_session_id() -> str | None:
    return _load().get("session_id")


def save_session_id(session_id: str) -> None:
    data = _load()
    data["session_id"] = session_id
    _save(data)


def clear_session_id() -> None:
    data = _load()
    data.pop("session_id", None)
    _save(data)
