# AI Meeting Assistant — Agent Instructions

## Project Context
AI Meeting Assistant converts meeting recordings into structured, searchable business information (transcripts, summaries, decisions, action items, RAG Q&A).

Source of truth — read before significant work:
- Problem definition: @docs/01_problem_definition.md
- Architecture: @docs/02_system_architecture.md
- Tech stack details: @docs/00_technology_stack.md
- Feature specs: @docs/features/<feature-name>.md

This file defines HOW the agent works. The `/docs` folder defines WHAT and WHY. 
Do not silently change product requirements or architecture. If a conflict
arises: stop, explain it, propose alternatives, wait for approval.

## Tech Stack (quick reference — full details in @docs/00_technology_stack.md)
Backend: Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Alembic
Frontend: React, Vite, TypeScript
AI: Whisper (STT), pyannote.audio (diarization), Gemini + LangChain (LLM/RAG),
Sentence Transformers (embeddings), Qdrant (vector DB)
Deployment: Docker + Docker Compose

Frontend must never access PostgreSQL, Qdrant, Whisper, or LLM providers directly — only through the FastAPI backend.

## Commands
Backend: pip install -r requirements.txt  →  uvicorn app.main:app --reload
Frontend: npm install  →  npm run dev
Full stack: docker compose up
Tests: pytest tests/ -q

## Repository Structure
backend/app/{api,core,models,schemas,services,repositories,pipelines}
frontend/src
data/{raw_audio, transcripts, eval_dataset}   — never commit real recordings
docs/{01_problem_definition, 02_system_architecture, 03_experiments,04_evaluation_report, features/}
prompts/   — LLM prompts live here, never hardcoded in Python
scripts/, tests/, docker/
assistant/  — local venv, never edit or commit

## Feature Workflow
1. Read the relevant docs + feature spec. If no spec exists, ask for one first.
2. Inspect existing code before changing it — don't rewrite working components.
3. Propose a short plan (files touched, API/DB changes, dependencies, tests) and wait for approval on anything non-trivial.
4. Implement only the requested scope — no unrelated refactoring.
5. Run tests and report real results. Never claim something works without actually running it.

## Hard Rules
- Never install/upgrade a dependency without explaining why and getting approval.
- Never run destructive commands (drops, resets, force pushes, deleting data) without explicit approval.
- Never commit: `.env`, API keys, secrets, real meeting recordings/transcripts, `/assistant`, `node_modules`.
- Never log full transcript content — metadata only (meeting ID, duration, status, timestamps, pipeline stage, error type, model name, request ID).
- Keep each AI pipeline stage as an independent module (transcription, diarization, summarization, retrieval) — never one giant file.
- Validate all LLM output with Pydantic schemas; never trust raw output.
- If evidence is insufficient for a RAG answer, say so — never invent an answer.

## Conventions
Python: type hints, PEP8, async for I/O-bound work.
API errors: `{ "error": "message" }` with correct HTTP status codes.
Git: Conventional Commits (feat/fix/docs/test/chore), commit after each working stage.

## Evaluation (for AI components — required, not optional)
Transcription: WER > 90% accuracy. Action items: precision > 80%.
RAG: retrieval + answer correctness. Record experiments in @docs/03_experiments.md, final results in @docs/04_evaluation_report.md.
"Works on my example" is not sufficient — evaluate against the eval dataset.

## Agent Behavior
Ask when requirements are ambiguous. Prefer small incremental changes.
Report failures honestly. Never silently change architecture, remove tests to make them pass, or claim success without verification.