import os
import warnings

# Suppress PyTorch internal warnings from Kokoro's model architecture
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
# Suppress HuggingFace Hub unauthenticated-request warning (model is cached locally)
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

import sounddevice as sd
import speech_recognition as sr
from kokoro import KPipeline

VOICE = "hf_alpha"  # American English female — most natural Kokoro voice
SPEED = 1.5

# Pipeline loaded once at import — model stays in memory for all subsequent calls
_pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")  # explicit repo suppresses warning


def list_microphones() -> list[tuple[int, str]]:
    names = sr.Microphone.list_microphone_names()
    return list(enumerate(names))


def recognize_speech_from_mic(mic_index: int) -> str:
    r = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 1
        print("Listening...")
        audio = r.listen(source)

    text = r.recognize_google(audio)
    print(f"You said: {text}")
    return text


def speak_text(text: str) -> None:
    # Kokoro splits long text into sentence chunks and yields each as it's ready,
    # so audio starts playing before the full text is synthesised.
    for _, _, audio in _pipeline(text, voice=VOICE, speed=SPEED):
        sd.play(audio.numpy(), samplerate=24000)
        sd.wait()
