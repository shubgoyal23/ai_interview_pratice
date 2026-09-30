import sys

from src.backends import AIBackend
from src.logger import SessionLogger
from src.prompts import build_system_prompt, split_feedback_response
from src.speech import recognize_speech_from_mic, speak_text


def run(
    backend: AIBackend,
    model: str,
    mic_index: int,
    feedback_on: bool,
    resume_text: str | None = None,
    resume_name: str | None = None,
) -> None:
    logger = SessionLogger.create(model, resume_name, feedback_on)
    print(f"Logging to: logs/{logger.path.name}\n")

    system_prompt = build_system_prompt(feedback_on, resume_text)

    print("Starting interview...\n")
    opening = backend.send(system_prompt)
    if not opening:
        print("No response from backend. Check credentials / connection.")
        sys.exit(1)

    current_question = opening
    print(f"Interviewer: {current_question}\n")
    speak_text(current_question)

    try:
        while True:
            try:
                print("Your turn (Ctrl+C to end)...")
                answer = recognize_speech_from_mic(mic_index)
            except KeyboardInterrupt:
                print(f"\nInterview ended. Log saved to: logs/{logger.path.name}")
                break
            except Exception as e:
                print(f"Could not understand audio: {e}. Try again.")
                continue

            if not answer:
                continue

            print("Thinking...")
            raw_response = backend.send(answer)
            if not raw_response:
                print("No response. Try again.")
                continue

            if feedback_on:
                feedback, next_question = split_feedback_response(raw_response)
                if feedback:
                    print(f"\nFeedback: {feedback}")
                    speak_text(feedback)
                print(f"\nInterviewer: {next_question}\n")
                speak_text(next_question)
                logger.log_entry(current_question, answer, feedback or None)
                current_question = next_question
            else:
                logger.log_entry(current_question, answer, None)
                current_question = raw_response
                print(f"\nInterviewer: {current_question}\n")
                speak_text(current_question)
    finally:
        backend.close()
        logger.close()
