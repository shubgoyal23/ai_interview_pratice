from src.prompts import MODELS
from src.speech import list_microphones, recognize_speech_from_mic, speak_text


def select_model(models: dict = MODELS) -> str:
    print("\nAvailable models:")
    for key, (model_id, label) in models.items():
        print(f"  {key}. {label}")
    choice = input("Select model [1]: ").strip() or "1"
    model_id, label = models.get(choice, models["1"])
    print(f"Using: {label}")
    return model_id


def _yes(prompt: str) -> bool:
    return input(f"{prompt} [Y/n]: ").strip().lower() in ("", "y", "yes")


def test_speaker() -> None:
    while True:
        print("\nSpeaker test — playing a short message...")
        speak_text("Hello! This is a speaker test. If you can hear me, your audio is working.")
        if _yes("Did you hear it clearly?"):
            return
        print("Check your volume and macOS output device (System Settings → Sound → Output).")
        if not _yes("Try again?"):
            return


def test_microphone(mic_index: int) -> bool:
    """Record one phrase and let the user confirm it was heard correctly."""
    while True:
        print("\nMic test — say something like: \"Testing one two three\"")
        try:
            text = recognize_speech_from_mic(mic_index)
        except Exception as e:
            print(f"Mic error: {e}")
            text = ""
        if text and _yes("Is that what you said?"):
            return True
        if not _yes("Try this mic again?"):
            return False


def select_microphone() -> int:
    while True:
        print("\nAvailable Microphones:")
        for index, name in list_microphones():
            print(f"  {index}: {name}")
        mic_index = int(input("Select microphone index: "))
        if test_microphone(mic_index):
            return mic_index
        print("Pick another microphone.")
