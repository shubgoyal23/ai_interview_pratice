import pyttsx3
import speech_recognition as sr

VOICE_ID = "com.apple.eloquence.en-US.Shelley"
RATE = 180  # words per minute

# Engine initialized once at import — no per-call process spawn or voice reload
_engine = pyttsx3.init()
_engine.setProperty("voice", VOICE_ID)
_engine.setProperty("rate", RATE)


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
    _engine.say(text)
    _engine.runAndWait()
