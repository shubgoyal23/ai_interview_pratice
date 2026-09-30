FEEDBACK_MARKER = "FEEDBACK:"
QUESTION_MARKER = "NEXTQUESTION:"

MODELS = {
    "1": ("auto",              "auto — task-optimized (default, 1.0x credits)"),
    "2": ("claude-sonnet-4.6", "Claude Sonnet 4.6 — best for interviews (1.3x credits)"),
    "3": ("claude-opus-4.8",   "Claude Opus 4.8 — most capable (2.2x credits)"),
    "4": ("claude-haiku-4.5",  "Claude Haiku 4.5 — fastest (0.4x credits)"),
    "5": ("deepseek-3.2",      "DeepSeek V3.2 — cheapest (0.25x credits)"),
}

CLAUDE_CLI_MODELS = {
    "1": ("default", "default — your Claude Code default model"),
    "2": ("sonnet",  "Claude Sonnet — best for interviews"),
    "3": ("opus",    "Claude Opus — most capable"),
    "4": ("haiku",   "Claude Haiku — fastest"),
}


def _base_prompt(feedback: bool) -> str:
    if feedback:
        return (
            "You are a senior interviewer conducting a job interview. "
            "Ask one focused question at a time. "
            "After each candidate answer, respond in EXACTLY this format — "
            "no extra text before or after:\n"
            "FEEDBACK: <one or two sentences evaluating the answer and how to improve it>\n"
            "NEXTQUESTION: <your next interview question>\n\n"
            "For your very first message (the greeting), just greet and ask the first question "
            "as plain text — no markers needed. "
            "Keep everything concise since responses will be spoken aloud."
        )
    return (
        "You are a senior interviewer conducting a job interview. "
        "Ask one focused question at a time. "
        "After each candidate answer, skip any feedback and immediately ask the next question. "
        "Start by greeting the candidate and asking your first question. "
        "Keep responses concise since they will be spoken aloud."
    )


def build_system_prompt(feedback: bool, resume_text: str | None) -> str:
    base = _base_prompt(feedback)
    if not resume_text:
        return base
    return (
        f"{base}\n\n"
        f"CANDIDATE RESUME:\n---\n{resume_text}\n---\n\n"
        "Tailor your questions to the candidate's specific background, skills, and experience."
    )


def split_feedback_response(response: str) -> tuple[str, str]:
    """Return (feedback, next_question). Falls back to ('', response) if markers are missing."""
    if FEEDBACK_MARKER not in response or QUESTION_MARKER not in response:
        return "", response
    fb_start = response.index(FEEDBACK_MARKER) + len(FEEDBACK_MARKER)
    nq_start = response.index(QUESTION_MARKER)
    feedback = response[fb_start:nq_start].strip()
    question = response[nq_start + len(QUESTION_MARKER):].strip()
    return feedback, question
