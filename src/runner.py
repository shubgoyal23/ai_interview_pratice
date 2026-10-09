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
    resumed: bool = False,
    resume_cmd: str | None = None,
) -> None:
    logger = SessionLogger.create(
        model, resume_name, feedback_on,
        session_id=backend.session_id, resume_cmd=resume_cmd, resumed=resumed,
    )
    print(f"Logging to: logs/{logger.path.name}")
    if backend.session_id:
        print(f"Session ID: {backend.session_id}")
    if resume_cmd:
        print(f"Resume later with: {resume_cmd}")
    print()

    if resumed:
        # The AI already has the system prompt and earlier answers in this session
        print("Resuming interview...\n")
        opening = backend.send(
            "The interview was paused and is now resuming. Keep the same interviewer "
            "role and format. Briefly welcome the candidate back, then re-ask the last "
            "unanswered question, or ask the next question if the last one was answered."
        )
    else:
        print("Starting interview...\n")
        opening = backend.send(build_system_prompt(feedback_on, resume_text))
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
