import argparse
import sys
from pathlib import Path

from src.resume import parse_resume
from src.runner import run
from src.setup import select_microphone, select_model


def main():
    parser = argparse.ArgumentParser(description="AI Interviewer powered by Kiro")
    parser.add_argument("--pdf", type=Path, help="Path to candidate resume PDF")
    parser.add_argument(
        "--feedback", action=argparse.BooleanOptionalAction, default=True,
        help="Enable per-answer feedback (default: on). Use --no-feedback to disable.",
    )
    args = parser.parse_args()

    resume_text = None
    resume_name = None
    if args.pdf:
        if not args.pdf.exists():
            print(f"Resume not found: {args.pdf}")
            sys.exit(1)
        print(f"Parsing resume: {args.pdf.name}")
        resume_text = parse_resume(args.pdf)
        resume_name = args.pdf.name
        print(f"Resume loaded ({len(resume_text)} chars, PII redacted)")

    feedback_on: bool = args.feedback
    print(f"Feedback: {'ON' if feedback_on else 'OFF'}")

    model = select_model()
    mic_index = select_microphone()

    run(
        model=model,
        mic_index=mic_index,
        feedback_on=feedback_on,
        resume_text=resume_text,
        resume_name=resume_name,
    )


if __name__ == "__main__":
    main()

# Usage:
#   uv run python main.py
#   uv run python main.py --pdf ~/Desktop/resume.pdf
#   uv run python main.py --pdf ~/Desktop/resume.pdf --no-feedback
#   uv run python main.py --no-feedback
