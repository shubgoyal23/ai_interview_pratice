import argparse
import sys
from pathlib import Path

from src.prompts import CLAUDE_CLI_MODELS, MODELS
from src.profile import load_profile
from src.runner import run
from src.setup import select_microphone, select_model, test_speaker

# ── Backend selector ──────────────────────────────────────────────────────────
# Change --backend value (or the default below) to switch AI provider.
# All backends share the same interface: send(prompt) → str, close() → None

BACKENDS = {
    "kiro":      "Kiro CLI          (kiro-cli, persistent session)",
    "claude":    "Claude CLI        (claude command, Claude Code)",
    "sgpt":      "GPT CLI           (sgpt / shell-gpt, needs OPENAI_API_KEY)",
    "ollama":    "Ollama            (local open-source, needs ollama running)",
    "openai":    "OpenAI API        (needs OPENAI_API_KEY)",
    "anthropic": "Anthropic API     (needs ANTHROPIC_API_KEY)",
}


def create_backend(name: str, model: str, session_id: str | None = None):
    if name == "kiro":
        from src.backends.kiro import KiroSession
        from src.config import get_session_id, save_session_id
        from src.backends.kiro import get_latest_session_id
        session_id = get_session_id()
        backend = KiroSession(model=model, session_id=session_id)
        if not session_id:
            new_id = get_latest_session_id()
            if new_id:
                save_session_id(new_id)
        return backend

    if name == "claude":
        from src.backends.claude_cli import ClaudeSession
        return ClaudeSession(model=model, session_id=session_id)

    if name == "sgpt":
        from src.backends.gpt_cli import SGPTSession
        return SGPTSession(model=model)

    if name == "ollama":
        from src.backends.ollama import OllamaSession
        return OllamaSession(model=model)

    if name == "openai":
        from src.backends.openai_api import OpenAISession
        return OpenAISession(model=model)

    if name == "anthropic":
        from src.backends.anthropic_api import AnthropicSession
        return AnthropicSession(model=model)

    print(f"Unknown backend: {name}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Interviewer")
    parser.add_argument(
        "--profile", type=Path,
        help="Path to candidate profile JSON (default: profile.json if it exists)",
    )
    parser.add_argument(
        "--feedback", action=argparse.BooleanOptionalAction, default=True,
        help="Enable per-answer feedback (default: on). Use --no-feedback to disable.",
    )
    parser.add_argument(
        "--backend", choices=list(BACKENDS), default="claude",
        help="AI backend to use (default: claude)",
    )
    parser.add_argument(
        "--resume", metavar="SESSION_ID",
        help="Continue an earlier interview (claude backend). The ID is in the log header.",
    )
    args = parser.parse_args()

    if args.resume and args.backend != "claude":
        print("--resume currently works only with --backend claude.")
        sys.exit(1)

    resume_text = None
    resume_name = None
    profile_path = args.profile or Path("profile.json")
    if args.profile and not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        sys.exit(1)
    if profile_path.exists():
        try:
            resume_text = load_profile(profile_path)
        except ValueError as e:
            print(e)
            sys.exit(1)
        resume_name = profile_path.name
        print(f"Profile loaded: {profile_path.name} ({len(resume_text)} chars, contact details omitted)")
    else:
        print("No profile.json found — running a general interview.")

    print(f"Backend: {BACKENDS[args.backend]}")
    print(f"Feedback: {'ON' if args.feedback else 'OFF'}")

    model = select_model(CLAUDE_CLI_MODELS if args.backend == "claude" else MODELS)
    test_speaker()
    mic_index = select_microphone()
    backend = create_backend(args.backend, model, session_id=args.resume)

    resume_cmd = None
    if args.backend == "claude":
        flags = [f"--backend claude --resume {backend.session_id}"]
        if args.profile:
            flags.append(f"--profile {args.profile}")
        if not args.feedback:
            flags.append("--no-feedback")
        resume_cmd = "uv run main.py " + " ".join(flags)

    run(
        backend=backend,
        model=model,
        mic_index=mic_index,
        feedback_on=args.feedback,
        resume_text=resume_text,
        resume_name=resume_name,
        resumed=bool(args.resume),
        resume_cmd=resume_cmd,
    )


if __name__ == "__main__":
    main()

# Usage:
#   uv run python main.py                                      # kiro (default)
#   uv run python main.py --backend anthropic                  # Anthropic API
#   uv run python main.py --backend openai                     # OpenAI API
#   uv run python main.py --backend ollama                     # local Ollama
#   uv run python main.py --backend claude                     # Claude Code CLI
#   uv run python main.py --backend sgpt                       # shell-gpt CLI
#   uv run python main.py --profile other.json --backend anthropic
#   uv run python main.py --no-feedback --backend openai
#   uv run python main.py --backend claude --resume <session-id>   # continue a past interview
