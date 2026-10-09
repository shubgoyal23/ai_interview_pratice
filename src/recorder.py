import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 24000   # Kokoro output rate; mic audio is resampled up to match
TURN_GAP = 0.4        # seconds of silence inserted between speakers


class Recorder:
    """Writes both sides of the interview, in turn order, to a single mono WAV file."""

    def __init__(self, path: Path):
        self.path = path
        # Written incrementally so the recording survives Ctrl+C
        self._wav = wave.open(str(path), "wb")
        self._wav.setnchannels(1)
        self._wav.setsampwidth(2)  # 16-bit PCM
        self._wav.setframerate(SAMPLE_RATE)
        self._last_source: str | None = None

    def add(self, audio: np.ndarray, sample_rate: int, source: str) -> None:
        """Append float audio in [-1, 1]. `source` ("ai"/"user") adds a gap when the speaker changes."""
        if self._last_source and self._last_source != source:
            self._wav.writeframes(np.zeros(int(SAMPLE_RATE * TURN_GAP), dtype=np.int16).tobytes())
        self._last_source = source

        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if sample_rate != SAMPLE_RATE and len(audio):
            n = int(len(audio) * SAMPLE_RATE / sample_rate)
            audio = np.interp(
                np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio,
            ).astype(np.float32)
        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        self._wav.writeframes(pcm.tobytes())

    def close(self) -> None:
        self._wav.close()
