# Project Guide

## Project

This is a Python 3.12+ FastAPI learning project for meeting summarization and LLM-backed agent features. Application code lives in `app/`; focused tests live in `tests/`; learning plans, acceptance criteria, and reading notes live in `docs/`.

## Development

- Use `uv` to manage dependencies and run Python commands. Project dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
- Run the test suite with `uv run --no-sync --offline pytest -v`.
- Automated tests must mock model clients and must not call external model services. Keep credentials in environment variables; `.env` files are ignored by Git.
- Preserve the existing FastAPI, Pydantic, pytest, and `LLMClient` patterns. Keep changes scoped to the relevant behavior and update focused tests when contracts change.
- Consult the relevant `docs/day-*.md` acceptance criteria before changing an in-progress learning task; planned work is not necessarily implemented.

## Application Map

- `app/api.py`: FastAPI routes and request validation.
- `app/llm/`: provider clients, shared interface, result schemas, and client factory.
- `app/prompts/`: prompts for application workflows.
- `tests/`: API behavior tests using mocked LLM clients.