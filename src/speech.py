import os
import re
import warnings

# Suppress PyTorch internal warnings from Kokoro's model architecture
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
# Suppress HuggingFace Hub unauthenticated-request warning (model is cached locally)
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

import sounddevice as sd
import speech_recognition as sr
from kokoro import KPipeline

VOICE = "af_heart"  # American English female — most natural Kokoro voice
SPEED = 1.2

PAUSE_THRESHOLD = 2 #pause_threshold

# Pipeline loaded once at import — model stays in memory for all subsequent calls
_pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")  # explicit repo suppresses warning


def list_microphones() -> list[tuple[int, str]]:
    names = sr.Microphone.list_microphone_names()
    return list(enumerate(names))


def recognize_speech_from_mic(mic_index: int) -> str:
    r = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = PAUSE_THRESHOLD
        print("Listening...")
        audio = r.listen(source)

    text = r.recognize_google(audio)
    print(f"You said: {text}")
    return text


def _normalise(text: str) -> list[str]:
    """Collapse single newlines into spaces; split on double newlines into paragraphs."""
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  # single \n → space
    text = re.sub(r' {2,}', ' ', text)             # clean up extra spaces
    return [p.strip() for p in text.split('\n\n') if p.strip()]


def speak_text(text: str) -> None:
    for para in _normalise(text):
        for _, _, audio in _pipeline(para, voice=VOICE, speed=SPEED):
            sd.play(audio.numpy(), samplerate=24000)
            sd.wait()
