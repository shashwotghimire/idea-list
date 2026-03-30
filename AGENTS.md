# AGENTS.md

Guidelines for agentic coding assistants working in `idea-list`.
This repo has a Python data pipeline, FastAPI backend, and React frontend.

## Project Snapshot

- Goal: curate side project ideas from Reddit/GitHub, enrich with Kimi AI, serve via API + UI.
- Core dirs: `pipeline/`, `api/`, `frontend/`.
- Data store: Neon PostgreSQL.
- Runtime baseline: Python 3.11+, Node 18+.

## Rule Sources (Cursor / Copilot)

Agents must check these files first:

- `.cursorrules`
- `.cursor/rules/**`
- `.github/copilot-instructions.md`

Current repo status (last check): none of the above files exist.
If they are added later, treat them as higher-priority instructions than this file.

## Environment

- Expected env files:
  - `pipeline/.env`
  - `api/.env`
  - `frontend/.env`
- Never commit env files or secret values.

## Build, Lint, Test Commands

Run from repository root unless noted.

### Pipeline (`pipeline/`)

- Setup:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r pipeline/requirements.txt`
- Run job:
  - `python pipeline/main.py`
- Lint:
  - `ruff check pipeline`
- Format:
  - `ruff format pipeline`
- Run all tests:
  - `pytest pipeline`
- Run one test file:
  - `pytest pipeline/tests/test_scraper.py`
- Run one test case:
  - `pytest pipeline/tests/test_scraper.py::test_extract_side_project`

### API (`api/`)

- Setup:
  - `pip install -r api/requirements.txt`
- Dev server:
  - `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
- Lint:
  - `ruff check api`
- Format:
  - `ruff format api`
- Type checking (if configured):
  - `mypy api`
- Run all tests:
  - `pytest api`
- Run one test file:
  - `pytest api/tests/test_ideas.py`
- Run one test case:
  - `pytest api/tests/test_ideas.py::test_get_ideas_filters`

### Frontend (`frontend/`)

- Setup:
  - `npm --prefix frontend install`
- Dev server:
  - `npm --prefix frontend run dev`
- Build:
  - `npm --prefix frontend run build`
- Preview:
  - `npm --prefix frontend run preview`
- Lint (if script exists):
  - `npm --prefix frontend run lint`
- Run all tests:
  - `npm --prefix frontend run test`
- Run one test file:
  - `npm --prefix frontend run test -- src/components/IdeaCard.test.jsx`
- Run one named test:
  - `npm --prefix frontend run test -- src/components/IdeaCard.test.jsx -t "renders title"`

### Suggested Local Verification Sequence

1. `ruff check pipeline api`
2. `ruff format --check pipeline api` (or run formatter)
3. `pytest pipeline api`
4. `npm --prefix frontend run build`
5. `npm --prefix frontend run test` (if tests exist)

## Code Style Guidelines

### General

- Keep diffs focused; avoid drive-by refactors.
- Follow existing architecture and naming before introducing new patterns.
- Add or update tests for behavior changes.
- Prefer explicit, readable code over clever shortcuts.

### Python (Pipeline + API)

- Follow PEP 8 and Ruff-compatible formatting.
- Use type hints for public functions, methods, and return values.
- Keep modules and functions single-purpose.
- Prefer `pathlib.Path` over string path manipulation.
- Use dataclasses/Pydantic models for structured payloads.

Imports:

- Order: standard library, third-party, local.
- Use absolute imports from project package roots.
- Avoid wildcard imports.

Naming:

- `snake_case`: variables, functions, modules.
- `PascalCase`: classes.
- `UPPER_SNAKE_CASE`: constants.

Error handling:

- Catch specific exceptions only.
- Never use bare `except:`.
- Re-raise with context when needed.
- API handlers should return consistent `HTTPException` messages and status codes.
- Log useful metadata (endpoint, source URL, IDs), never secrets.

### FastAPI Conventions

- Keep request/response schemas in `models.py` (or schema modules).
- Keep route handlers thin; move business/data logic to helpers/services.
- Validate query params with typed signatures and constraints.
- Keep pagination defaults stable (`limit`, `offset`).
- Preserve response shape compatibility unless versioning intentionally changes it.

### SQL / Database

- Use parameterized queries only.
- Deduplicate deterministically (use `source_url` policy consistently).
- Validate enum-like fields (`difficulty`, `source`) in one place.
- Prefer idempotent writes so pipeline reruns are safe.

### React / JavaScript

- Use functional components and hooks.
- Keep data-fetching/state logic separated from presentational components.
- Centralize API calls in `frontend/src/api.js` (or equivalent service module).

Imports:

- Order: external libs, internal modules, styles/assets.

Naming:

- `PascalCase`: components.
- `camelCase`: functions, variables, props.
- Component filename should match default export name.

UI behavior:

- Handle loading, empty, and error states explicitly.
- Avoid deep prop drilling; lift state or use shared context when appropriate.

### Formatting and Docs

- Target line length: Python ~88-100, JS/MD ~100-120.
- Add concise docstrings/comments only for non-obvious behavior.
- Comments should explain why, not what.
- Keep markdown instructions command-first and copy/paste friendly.

## Testing Guidelines

- Prefer deterministic tests.
- Unit tests should mock external systems (Reddit, GitHub, Kimi, DB).
- Integration tests should use disposable data and cleanup.
- Add regression tests for bug fixes when practical.

## Agent Workflow

- Before edits: inspect nearby files for patterns and scripts.
- During edits: change only relevant files.
- After edits: run targeted tests first, then broader checks.
- After each completed feature: commit and push directly to `main`.
- In change notes: include exact commands run and outcomes.

## Security and Secrets

- Never print or commit API keys, tokens, or connection strings.
- Treat AI/model output as untrusted input; validate before DB insert.
- Sanitize any user-provided text rendered in the frontend.

## If Commands Drift

If commands here fail, verify current tooling in:

- `frontend/package.json`
- `pipeline/requirements.txt`
- `api/requirements.txt`
- `README.md`

Then update this file in the same change.
