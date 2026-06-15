import sys

from src.config import get_session_id, save_session_id
from src.kiro import get_latest_session_id, query_kiro
from src.logger import SessionLogger
from src.prompts import build_system_prompt, split_feedback_response
from src.speech import recognize_speech_from_mic, speak_text


def run(
    model: str,
    mic_index: int,
    feedback_on: bool,
    resume_text: str | None = None,
    resume_name: str | None = None,
) -> None:
    logger = SessionLogger.create(model, resume_name, feedback_on)
    print(f"Logging to: logs/{logger.path.name}\n")

    session_id = get_session_id()
    if session_id:
        print(f"Resuming session: {session_id}\n")
        opening = query_kiro("Continue the interview from where we left off.", model=model, session_id=session_id)
    else:
        system_prompt = build_system_prompt(feedback_on, resume_text)
        print("Starting interview — connecting to Kiro...\n")
        opening = query_kiro(system_prompt, model=model)
        new_id = get_latest_session_id()
        if new_id:
            save_session_id(new_id)
            print(f"Session saved: {new_id}\n")

    if not opening:
        logger.close()
        print("No response from Kiro. Run `kiro-cli whoami` to check login status.")
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

            print("Kiro thinking...")
            raw_response = query_kiro(answer, model=model, session_id=get_session_id())
            if not raw_response:
                print("No response from Kiro.")
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
        logger.close()
