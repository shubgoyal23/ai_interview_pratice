import io
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"


class SessionLogger:
    def __init__(self, log_path: Path, file: io.TextIOWrapper):
        self.path = log_path
        self._file = file

    @classmethod
    def create(cls, model: str, resume_name: str | None, feedback_on: bool) -> "SessionLogger":
        LOG_DIR.mkdir(exist_ok=True)
        version = len(list(LOG_DIR.glob("interview_v*.log"))) + 1
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = LOG_DIR / f"interview_v{version:03d}_{ts}.log"

        # Open once for the whole session; line-buffered so each \n flushes to OS
        file = log_path.open("w", buffering=1)
        logger = cls(log_path, file)
        logger._write_header(model, resume_name, feedback_on)
        return logger

    def _write_header(self, model: str, resume_name: str | None, feedback_on: bool) -> None:
        self._write("=" * 50)
        self._write(f"Interview Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write(f"Model: {model}")
        self._write(f"Feedback: {'on' if feedback_on else 'off'}")
        if resume_name:
            self._write(f"Resume: {resume_name}")
        self._write("=" * 50)
        self._write("")

    def _write(self, line: str) -> None:
        self._file.write(line + "\n")

    def log_entry(self, question: str, answer: str, feedback: str | None) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._write(f"[{ts}]")
        self._write(f"Question: {question}")
        self._write(f"Answer: {answer}")
        if feedback:
            self._write(f"Feedback: {feedback}")
        self._write("")

    def close(self) -> None:
        self._file.flush()
        self._file.close()
