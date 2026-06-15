# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

JobSearch AI is a tool that generates tailored cover letters and a fit analysis from a resume and a job description, using OpenAI's API.

Current feature set (as implemented):

- **Save and reuse resumes** — `POST /api/resumes` (JSON `{label, content}`) and `GET /api/resumes` / `GET /api/resumes/{id}` ([backend/app/api/routes/resume.py](backend/app/api/routes/resume.py)). Both `POST /api/resumes` and `POST /api/resumes/upload` reject a `label` that already exists (case-insensitive) with a 400 `"A resume already exists with this name."` ([backend/app/repositories/resume_repo.py](backend/app/repositories/resume_repo.py) `get_by_label`).
- **Upload a resume as a PDF** — `POST /api/resumes/upload` (`multipart/form-data` with `label` and `file`). Extracts text via `PyPDF2` ([backend/app/services/resume_parser.py](backend/app/services/resume_parser.py)) and stores it the same as `POST /api/resumes`. Rejects non-PDF files and PDFs with no extractable text (e.g. scanned images) with a 400. This is the endpoint the frontend uses.
- **Delete a saved resume** — `DELETE /api/resumes/{id}` returns 204, or 404 if not found. If the resume is referenced by an existing cover letter (FK on `cover_letters.resume_id`), returns 400 `"This resume is used by saved cover letters and can't be deleted."` instead of deleting. API-only — not exposed in the UI (deleting history entries is the supported way to free up a resume for deletion).
- **Generate a tailored cover letter + fit analysis** — `POST /api/cover-letter` accepts either a saved `resume_id` or pasted `resume_text`, plus a `role_title` and `job_description`. Calls OpenAI in JSON mode and persists the result ([backend/app/api/routes/cover_letter.py](backend/app/api/routes/cover_letter.py), [backend/app/services/generator.py](backend/app/services/generator.py))
- **Generation history** — `GET /api/cover-letter` returns past generations
- **Delete a history entry** — `DELETE /api/cover-letter/{id}` returns 204, or 404 if not found. Deletes the `CoverLetter` row and its associated `Role` row (each generation creates its own `Role`, so it's safe to remove alongside the cover letter — [backend/app/services/generator.py](backend/app/services/generator.py) `CoverLetterService.delete_history_entry`). Exposed in the UI as a "Delete" button on each History entry.
- **Health check** — `GET /health`, used for deploy/monitoring checks ([backend/app/api/routes/health.py](backend/app/api/routes/health.py))

The frontend ([frontend/](frontend/)) is a minimal React UI for the flows above — upload/select a resume, paste a job description, generate a cover letter + fit analysis, browse past generations, and delete history entries. The UI uses a "warm vintage paper" retro theme (cream/parchment background, serif headings, terracotta/olive/mustard accents — see [frontend/src/index.css](frontend/src/index.css) and [frontend/src/App.css](frontend/src/App.css)) and shows an animated progress bar ([frontend/src/components/LoadingBar.jsx](frontend/src/components/LoadingBar.jsx)) while a cover letter is generating. See [frontend/README.md](frontend/README.md) for stack and security notes.

## Tech stack

### Backend (`backend/`)

- **Python** (venv at `backend/venv/`, compiled artifacts show `cpython-312` — Python 3.12)
- **FastAPI** (`fastapi>=0.110.0`) — web framework, app factory in [backend/app/main.py](backend/app/main.py)
- **Uvicorn** (`uvicorn>=0.29.0`) — ASGI server (`uvicorn app.main:app --reload`)
- **SQLAlchemy** (`sqlalchemy>=2.0.0`) — ORM, declarative models in `app/models/`, using SQLAlchemy 2.0 `Mapped`/`mapped_column` style
- **Pydantic / pydantic-settings** (`pydantic>=2.0.0`, `pydantic-settings>=2.0.0`) — request/response schemas (`app/schemas/`) and settings (`app/core/config.py`)
- **Alembic** (`alembic>=1.13.0`) — initialized in [backend/alembic/](backend/alembic/) (config at [backend/alembic.ini](backend/alembic.ini)). `env.py` imports `app.models`/`app.db.base.Base` for autogenerate and reads the DB URL from `app.core.config.settings.database_url` — no DB config is duplicated in `alembic.ini`. Run `alembic upgrade head` from `backend/` to apply migrations (this replaced the old `Base.metadata.create_all` dev bootstrap, which has been removed from `app/main.py`). For new schema changes: edit the models, then `alembic revision --autogenerate -m "..."` and review the generated migration before committing.
- **psycopg2-binary** (`psycopg2-binary>=2.9.0`) — PostgreSQL driver
- **python-dotenv** (`python-dotenv>=1.0.0`) — loads `.env` (via pydantic-settings' `env_file` support)
- **python-multipart** (`python-multipart>=0.0.9`) — enables `UploadFile`/`File`/`Form` parsing for `POST /api/resumes/upload` ([backend/app/api/routes/resume.py](backend/app/api/routes/resume.py))
- **PyPDF2** (`pypdf2>=3.0.0`) — extracts text from uploaded resume PDFs in [backend/app/services/resume_parser.py](backend/app/services/resume_parser.py)
- **OpenAI SDK** (`openai>=1.30.0`) — used in [backend/app/services/generator.py](backend/app/services/generator.py) to call the Chat Completions API in JSON mode

Database: PostgreSQL (`postgresql+psycopg2://...`). Default in [backend/app/core/config.py](backend/app/core/config.py) points at local Postgres; Railway injects `DATABASE_URL` in production.

### Frontend (`frontend/`)

- **React 18.3.1** + **react-dom 18.3.1**
- **Vite 6.4.3** + **@vitejs/plugin-react 5.2.0** — dev server and build tool ([frontend/vite.config.js](frontend/vite.config.js)). Pinned below the latest major versions for compatibility with the installed Node.js version (20.11.0); Vite 8/rolldown requires Node 20.19+/22.12+.
- **ESLint 9** with `@eslint/js`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` ([frontend/eslint.config.js](frontend/eslint.config.js)). `react/prop-types` is disabled (no PropTypes/TypeScript in this project).
- No router or state management library — a small `src/api/` client wraps `fetch`, and component state is managed with React hooks. `VITE_API_URL` (see [frontend/.env.example](frontend/.env.example)) points at the backend.

## Project structure

Backend layers, each with a single responsibility:

- **`app/api/routes/`** — FastAPI routers (HTTP layer only). Parses/validates requests via schemas, calls services or repositories, and maps results/exceptions to HTTP responses. No business logic or direct DB queries.
- **`app/services/`** — business logic. `CoverLetterService` orchestrates resume resolution, role creation, the OpenAI call, and persistence; `resume_parser.py` extracts text from uploaded resume PDFs (`extract_resume_text`). Knows nothing about HTTP or FastAPI.
- **`app/repositories/`** — data access layer. One repository per model (`ResumeRepository`, `RoleRepository`, `CoverLetterRepository`); each is the *only* code that runs SQLAlchemy queries against its model.
- **`app/models/`** — SQLAlchemy ORM models (`Resume`, `Role`, `CoverLetter`), all inheriting from `Base` in `app/db/base.py`. Imported in `backend/alembic/env.py` (`import app.models`) so they register with `Base.metadata` for autogenerate.
- **`app/schemas/`** — Pydantic models defining API request/response contracts (`ResumeCreate`/`ResumeRead`, `GenerateCoverLetterRequest`/`CoverLetterRead`, `CoverLetterBody`, `FitAnalysis`). Also define the exact JSON shape the LLM must return.
- **`app/db/`** — `base.py` (declarative `Base`), `session.py` (engine, `SessionLocal`, `get_db` FastAPI dependency).
- **`app/core/config.py`** — the single `Settings` object (pydantic-settings), loaded from `backend/.env`. This is the **only** place environment variables are read.

### Frontend (`frontend/`)

- **`src/api/`** — `client.js` (shared `fetch` wrapper: JSON, `FormData`, and `DELETE` requests via `get`/`post`/`postForm`/`del`, error handling), `resumes.js` (`getResumes`, `uploadResume`), `coverLetters.js` (`generateCoverLetter`, `getCoverLetterHistory`, `deleteCoverLetter`).
- **`src/components/`** — `GenerateForm.jsx` (resume mode toggle: upload a new PDF resume + label, or pick from saved resumes; plus role title + job description, generate; shows `LoadingBar` while generating), `ResultView.jsx` (renders a cover letter + fit analysis), `HistoryList.jsx` (past generations, expandable, each with a delete button), `LoadingBar.jsx` (animated progress bar shown during generation).
- **`src/App.jsx`** — tab navigation (`generate` / `history`) and shared state (saved resumes list, last result, history refresh trigger).
- **`.env.example`** — `VITE_API_URL`, copied to `.env.local` (gitignored) for local dev.

## Architecture decisions

- **SQLAlchemy models vs. Pydantic schemas are kept separate.** Models (`app/models/`) describe how data is stored; schemas (`app/schemas/`) describe how data looks over the API. This lets the API contract evolve independently of the table structure (e.g. `CoverLetterRead` decomposes the `cover_letter`/`fit_analysis` JSON columns into typed `CoverLetterBody`/`FitAnalysis` schemas) and prevents accidentally leaking ORM internals (relationships, lazy-loaded attributes) over the wire.

- **Business logic lives in `app/services/`, not in routes.** Routes ([backend/app/api/routes/cover_letter.py](backend/app/api/routes/cover_letter.py)) are thin: they validate input via schemas, delegate to a service, and translate exceptions to HTTP status codes. `CoverLetterService` ([backend/app/services/generator.py](backend/app/services/generator.py)) contains the actual orchestration (resolve resume → create role → call OpenAI → persist). This keeps the logic testable without spinning up FastAPI, and reusable if a second entry point (CLI, background job) is ever added.

- **Database queries are isolated in `app/repositories/`.** Services depend on repository classes (`ResumeRepository`, `RoleRepository`, `CoverLetterRepository`) rather than calling `db.query(...)` directly. Each repository is the single place that knows the query shape for its model, making it easy to change storage details (e.g. add caching, change ordering, swap ORM calls) without touching business logic.

- **`generate_cover_letter()` is a pure function, separate from `CoverLetterService`.** It takes plain strings and returns a dict from the OpenAI call, with no DB session — making it straightforward to unit test and mock.

## Python conventions to follow

- **All settings and environment variables go through [backend/app/core/config.py](backend/app/core/config.py)**, via the `Settings` class (pydantic-settings `BaseSettings`) and the `settings` singleton. Never call `os.environ` / `os.getenv` directly anywhere else.
- **Use type hints on all function signatures** — existing code already does this consistently (e.g. `def get(self, resume_id: int) -> Resume | None`); keep it up for new code.
- **Use async functions for all route handlers and service methods.** Note: the current route handlers and service methods (e.g. `create_resume`, `CoverLetterService.generate`) are defined as `def`, not `async def`. Treat `async def` as the standard for *new* code, and consider migrating existing handlers when they're touched (the OpenAI SDK and SQLAlchemy both support async clients/sessions if this conversion happens).
- **Pydantic schemas handle all input validation.** Routes and services should only work with validated schema instances (`ResumeCreate`, `GenerateCoverLetterRequest`, etc.) — never read raw `Request` bodies or untyped dicts from client input.

## Security rules (non-negotiable)

- Never hardcode secrets, API keys, or credentials in code.
- Never log or print sensitive values (API keys, tokens, passwords, full `.env` contents).
- All secrets must be loaded from environment variables via `app/core/config.py` only.
- `.env` must never be committed. Currently covered by [.gitignore](.gitignore): `backend/.env`, `frontend/.env`, `frontend/.env.local`, plus root `.env`.
- Passwords must never be stored or returned in plain text. (No user/auth model exists yet — apply this when one is added.)
- API responses must never expose internal-only fields (e.g. `hashed_password`, internal security IDs) or raw error stack traces in production. Note: [backend/app/api/routes/cover_letter.py](backend/app/api/routes/cover_letter.py) currently returns `str(e)` from a bare `except Exception` as a 500 detail — this should be replaced with a generic message plus server-side logging before production use.
- Always use the SQLAlchemy ORM (as the repositories already do) — never build raw SQL strings with interpolated user input.

## Environment variables

Defined in [backend/app/core/config.py](backend/app/core/config.py) (`Settings`), loaded from `backend/.env`:

| Variable | Used for | In `.env.example`? |
|---|---|---|
| `OPENAI_API_KEY` | Authenticates calls to the OpenAI API in `generate_cover_letter()` | Yes — currently `your-key-here` |
| `OPENAI_MODEL` | Model used for cover letter generation (default `gpt-4o`) | Yes — currently `gpt-4o` |
| `DATABASE_URL` | SQLAlchemy connection string for Postgres (default local Postgres; Railway sets this in production) | Yes — currently a local Postgres URL |

[backend/.env.example](backend/.env.example) provides sensible non-secret defaults for `OPENAI_MODEL` and `DATABASE_URL`, with `OPENAI_API_KEY` left as a placeholder — keep it this way; only the API key needs to stay redacted.

CORS origins (`Settings.cors_origins`) are currently hardcoded in `config.py` rather than environment-driven (`http://localhost:5173` for Vite dev, plus the production Netlify URL — see Deployment below).

## Local development

A [docker-compose.yml](docker-compose.yml) at the repo root runs a local Postgres (`postgres:16-alpine`, db `jobsearch`, user/pass `postgres`/`postgres`, port 5432) matching the default `DATABASE_URL`. To run the backend locally:

```
docker compose up -d
cd backend
.\venv\Scripts\activate
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend (`frontend/`)

```
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Runs at `http://localhost:5173` (already allowed by `Settings.cors_origins`). Requires the backend running per above. See [frontend/README.md](frontend/README.md) for the stack summary and security notes.

## Deployment

- **Frontend**: Netlify — https://jobsearch-ai.netlify.app (deploys from `main`, base directory `frontend`, build command `npm run build`, publish directory `dist`, env var `VITE_API_URL` set to the Railway backend URL)
- **Backend**: Railway — https://jobsearch-ai-production.up.railway.app (root directory `backend`, env vars `OPENAI_API_KEY`, `OPENAI_MODEL`, `DATABASE_URL`; `DATABASE_URL` is a reference to the linked Railway Postgres service)
- **Database**: Railway Postgres (production — separate from the local docker-compose Postgres used in development)
- **Migrations**: after schema changes, run `alembic upgrade head` against production via the Railway service's Console tab (this does not happen automatically)

## What not to do

- Do not put business logic in route handlers — it belongs in `app/services/`.
- Do not put database queries in services — they belong in `app/repositories/`.
- Do not import or call `os.environ`/`os.getenv` directly — use `settings` from `app/core/config.py`.
- Do not expose internal error details (stack traces, raw exception strings) in API responses.
- Do not commit `.env`, `venv/`, `__pycache__/`, `node_modules/`, or `dist/` (already covered by [.gitignore](.gitignore)).
