from src.prompts import MODELS
from src.speech import list_microphones


def select_model() -> str:
    print("\nAvailable models:")
    for key, (model_id, label) in MODELS.items():
        print(f"  {key}. {label}")
    choice = input("Select model [1]: ").strip() or "1"
    model_id, label = MODELS.get(choice, MODELS["1"])
    print(f"Using: {label}")
    return model_id


def select_microphone() -> int:
    print("\nAvailable Microphones:")
    for index, name in list_microphones():
        print(f"  {index}: {name}")
    return int(input("Select microphone index: "))
