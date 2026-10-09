# AI Interviewer

A voice-based mock interviewer that runs in your terminal. It asks questions out loud, listens to your spoken answers, and (optionally) gives feedback on each answer before moving on. Questions are tailored to your background from `profile.json`.

Speech runs locally: text-to-speech uses [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) and speech-to-text uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Only the interview conversation goes to the AI backend you choose.

## Requirements

- macOS (built on Apple Silicon)
- [uv](https://docs.astral.sh/uv/) — installs Python 3.12 and all dependencies
- A microphone and speakers/headphones
- One AI backend (see [Backends](#backends))

If `pyaudio` fails to install, run `brew install portaudio` and try again.

## Quick start

```bash
uv run main.py
```

The first run downloads the voice and speech-recognition models; later runs work offline (apart from the AI backend).

On startup you will:

1. Pick a model for the chosen backend.
2. Hear a **speaker test** and confirm you heard it.
3. Pick a microphone and do a **mic test** — your words appear live as you speak; confirm they're right.
4. Start the interview. Answer out loud; pause for 2 seconds to finish your answer. Press `Ctrl+C` to end.

## Options

```bash
uv run main.py --backend anthropic          # choose AI backend (default: claude)
uv run main.py --profile other.json         # use a different profile (default: profile.json)
uv run main.py --no-feedback                # skip per-answer feedback
uv run main.py --resume <session-id>        # continue an earlier interview (claude backend)
```

### Resuming an interview

With the `claude` backend, each interview gets a session ID. It's printed at startup and written to the top of the log file, along with the exact command to continue:

```
Session ID: a7d56585-3a65-4761-8192-40f8d9e25e08
Resume with: uv run main.py --backend claude --resume a7d56585-3a65-4761-8192-40f8d9e25e08
```

Running that command picks up where you stopped. The AI remembers earlier questions and answers, and re-asks the last unanswered question. The resumed part goes into a new log file with the same session ID.

## Candidate profile

Put your background in `profile.json` in the project root. It follows the [JSON Resume](https://jsonresume.org/schema) format plus a `profile.jobPreferences` section (roles, years of experience, notice period, preferred locations, and so on). The full schema is in [src/profile_schema.json](src/profile_schema.json).

- The file is validated against the schema on startup; any mistake (a misspelled field, a negative number) is reported and the app exits.
- Without a `profile.json`, you get a general interview.
- **Never sent to the AI:** email, phone, photo, street address, postal code, profile links, date of birth, gender, current/expected CTC, and references.
- `profile.json` is git-ignored because it holds personal details.

## Backends

| `--backend` | What it uses | Setup |
|---|---|---|
| `claude` (default) | Claude Code CLI | [Install Claude Code](https://claude.ai/code) and log in |
| `anthropic` | Anthropic API | `export ANTHROPIC_API_KEY=...` |
| `openai` | OpenAI API | `export OPENAI_API_KEY=...` |
| `ollama` | Local open-source models | [Install Ollama](https://ollama.com) and keep it running |
| `sgpt` | shell-gpt CLI | `pip install shell-gpt` and `export OPENAI_API_KEY=...` |
| `kiro` | Kiro CLI | Install `kiro-cli` and log in |

The model list shown at startup is specific to the `claude` backend; other backends currently share the Kiro model list.

## Logs

Each interview is saved to `logs/interview_vNNN_<timestamp>.log` with every question, your answer, and any feedback. The `logs/` folder is git-ignored.

## Tuning speech

Settings at the top of [src/speech.py](src/speech.py):

| Setting | Default | What it does |
|---|---|---|
| `VOICE` | `af_heart` | Kokoro voice |
| `SPEED` | `1.2` | Speaking speed |
| `PAUSE_THRESHOLD` | `2` | Seconds of silence that end your answer |
| `WHISPER_MODEL` | `base.en` | Speech-recognition model; `small.en` is more accurate but the live preview is slower |
| `LIVE_INTERVAL` | `0.8` | Seconds between live transcript updates |

## Project layout

```
main.py                 entry point: options, setup, starts the interview
profile.json            your candidate profile (git-ignored)
src/
  runner.py             interview loop
  speech.py             text-to-speech, live speech-to-text, mic listing
  setup.py              model picker, speaker and mic tests
  profile.py            profile.json validation and formatting
  profile_schema.json   profile JSON schema
  prompts.py            system prompt and model lists
  logger.py             interview log files
  config.py             saved Kiro session id (config.json)
  backends/             one file per AI backend
temp/                   standalone tools (own uv project)
  transcribe.py         audio file → text (local Whisper)
  speach.py             input.txt → spoken audio + output.wav (Kokoro)
```

## Troubleshooting

- **Words aren't picked up / answer never ends** — background noise may be above the silence threshold. Re-run the mic test in a quieter spot or use a headset mic.
- **No response from backend** — check the backend's setup in [Backends](#backends) (API key set, CLI logged in, Ollama running).
- **`profile.json does not match the schema`** — the message lists each bad field; fix those and re-run.
