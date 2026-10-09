import os
import queue
import re
import shutil
import sys
import threading
import time
import warnings

# Suppress PyTorch internal warnings from Kokoro's model architecture
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
# Suppress HuggingFace Hub unauthenticated-request warning (model is cached locally)
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

import numpy as np
import sounddevice as sd
import speech_recognition as sr
from faster_whisper import WhisperModel
from kokoro import KPipeline

from src.recorder import Recorder

VOICE = "af_heart"  # American English female — most natural Kokoro voice
# VOICE = "hf_alpha"  # hindi voice
SPEED = 1.2

PAUSE_THRESHOLD = 2 #pause_threshold

# Local speech-to-text. "base.en" is fast enough to re-transcribe live;
# use "small.en" for better accuracy at the cost of a slower live preview.
WHISPER_MODEL = "base.en"
SAMPLE_RATE_IN = 16000   # Whisper expects 16 kHz mono
LIVE_INTERVAL = 0.8      # seconds between live preview updates

# Pipeline loaded once at import — model stays in memory for all subsequent calls
_pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")  # explicit repo suppresses warning
_whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


def list_microphones() -> list[tuple[int, str]]:
    names = sr.Microphone.list_microphone_names()
    return list(enumerate(names))


def _transcribe(audio: np.ndarray, final: bool = False) -> str:
    segments, _ = _whisper.transcribe(
        audio, language="en", beam_size=5 if final else 1, vad_filter=final,
        condition_on_previous_text=False,
    )
    return " ".join(seg.text.strip() for seg in segments).strip()


def _show_live(text: str) -> None:
    """Redraw the live transcript on one line, keeping the latest words visible."""
    width = shutil.get_terminal_size().columns - 1
    line = f"... {text}"
    if len(line) > width:
        line = "... " + text[-(width - 4):]
    sys.stdout.write("\r\033[K" + line)
    sys.stdout.flush()


def recognize_speech_from_mic(mic_index: int, recorder: Recorder | None = None) -> str:
    r = sr.Recognizer()
    chunks: queue.Queue[np.ndarray] = queue.Queue()
    stop = threading.Event()

    with sr.Microphone(device_index=mic_index, sample_rate=SAMPLE_RATE_IN) as source:
        r.adjust_for_ambient_noise(source)
        threshold = r.energy_threshold

        # Read the mic on a separate thread so no audio is dropped while Whisper runs
        def reader():
            while not stop.is_set():
                data = source.stream.read(source.CHUNK)
                chunks.put(np.frombuffer(data, dtype=np.int16))

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        print("Listening... (speak now, pause to finish)")

        buffer: list[np.ndarray] = []
        started = False
        silence = 0.0
        last_update = time.monotonic()
        try:
            while True:
                chunk = chunks.get()
                rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                if not started:
                    if rms < threshold:
                        continue
                    started = True
                buffer.append(chunk)
                silence = silence + len(chunk) / SAMPLE_RATE_IN if rms < threshold else 0.0
                if silence >= PAUSE_THRESHOLD:
                    break
                # Skip a preview if transcription is falling behind the mic
                if time.monotonic() - last_update >= LIVE_INTERVAL and chunks.qsize() < 4:
                    audio = np.concatenate(buffer).astype(np.float32) / 32768
                    _show_live(_transcribe(audio))
                    last_update = time.monotonic()
        finally:
            stop.set()
            thread.join()

    audio = np.concatenate(buffer).astype(np.float32) / 32768
    if recorder:
        recorder.add(audio, SAMPLE_RATE_IN, "user")
    text = _transcribe(audio, final=True)
    sys.stdout.write("\r\033[K")
    print(f"You said: {text}")
    return text


def _strip_markdown(text: str) -> str:
    """Remove markdown syntax so the voice reads plain words (e.g. **English** → English)."""
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)          # code blocks
    text = re.sub(r'`([^`]*)`', r'\1', text)                         # inline code
    text = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', text)           # links / images
    text = re.sub(r'(\*\*|__)(.+?)\1', r'\2', text)                  # bold
    text = re.sub(r'(?<!\w)([*_])(?!\s)(.+?)(?<!\s)\1(?!\w)', r'\2', text)  # italic
    text = re.sub(r'~~(.+?)~~', r'\1', text)                         # strikethrough
    text = re.sub(r'^\s{0,3}#{1,6}\s*', '', text, flags=re.MULTILINE)       # headings
    text = re.sub(r'^\s*(?:[-*+]|\d+[.)])\s+', '', text, flags=re.MULTILINE)  # list markers
    text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)          # blockquotes
    return text


def _normalise(text: str) -> list[str]:
    """Collapse single newlines into spaces; split on double newlines into paragraphs."""
    text = _strip_markdown(text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  # single \n → space
    text = re.sub(r' {2,}', ' ', text)             # clean up extra spaces
    return [p.strip() for p in text.split('\n\n') if p.strip()]


def speak_text(text: str, recorder: Recorder | None = None) -> None:
    for para in _normalise(text):
        for _, _, audio in _pipeline(para, voice=VOICE, speed=SPEED):
            if recorder:
                recorder.add(audio.numpy(), 24000, "ai")
            sd.play(audio.numpy(), samplerate=24000)
            sd.wait()
