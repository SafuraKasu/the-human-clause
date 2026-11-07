# The Human Clause: ITU Global AI Hackathon prototype

Hackathon prototype. Priorities: a working end-to-end demo, a focused scope, and a clear pitch.

## Context (loaded automatically)
@docs/competition.md
@docs/build-prompt.md

`docs/master-prompt.md` is the teammate's original full spec, kept as reference only. It is not auto-loaded and not the active spec; read it on demand.

## Working rules
- Build a thin vertical slice first, then deepen it. Always keep something demoable.
- Commit at every working state.
- Record decisions in `docs/decisions.md` (one line each) so every session and agent stays aligned.
- Stack and run commands: see the "Stack" section below. Update it as soon as they are chosen.

## Stack
Python 3.13, FastAPI, SQLite, React (Vite). LLM via free OpenAI-compatible provider (see `.env.example`).

## Run / test
- Build the policy KB: `python backend/kb/ingest.py` (needs `pip install -r backend/requirements.txt`)
- LLM smoke test: set `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, then `python backend/scripts/llm_smoke_test.py`

## Agents
- `qa-tester` (`.claude/agents/qa-tester.md`): runs the app, tests the demo flow and edge cases, and reports bugs. It does not fix them.
