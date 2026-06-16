# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

JobSearch AI generates tailored cover letters, fit analyses, and "Why This Company" answers from a resume and job description. See [README.md](README.md) for user-facing documentation and local dev setup.

## API surface (quick reference)

| Method | Path | Auth required |
|---|---|---|
| `GET` | `/api/auth/{provider}/login` | — |
| `GET` | `/api/auth/{provider}/callback` | — |
| `GET` | `/api/auth/me` | cookie |
| `POST` | `/api/auth/logout` | cookie |
| `GET/POST` | `/api/resumes`, `/api/resumes/upload` | approved |
| `GET/DELETE` | `/api/resumes/{id}` | approved |
| `POST/GET` | `/api/cover-letter` | approved |
| `DELETE` | `/api/cover-letter/{id}` | approved |
| `GET` | `/api/admin/users` | admin |
| `POST` | `/api/admin/users/{id}/approve` | admin |
| `POST` | `/api/admin/users/{id}/reject` | admin |
| `GET` | `/health` | — |

`POST /api/cover-letter` flags: `generate_cover_letter` (default `true`), `generate_why_this_company` (default `false`). `cover_letter`, `fit_analysis`, and `why_this_company` on `CoverLetterRead` are all nullable — any output can be skipped.

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
- **Authlib** (`authlib>=1.3.0`) — OAuth client registry for Google/Microsoft (OIDC discovery) in [backend/app/core/oauth.py](backend/app/core/oauth.py); requires Starlette's `SessionMiddleware` (registered in `main.py`) for state/nonce during the redirect.
- **PyJWT** (`pyjwt>=2.8.0`) — signs/verifies the `access_token` cookie in [backend/app/core/security.py](backend/app/core/security.py)
- **itsdangerous** (`itsdangerous>=2.1.0`) — required by Starlette's `SessionMiddleware`

Database: PostgreSQL (`postgresql+psycopg2://...`). Default in [backend/app/core/config.py](backend/app/core/config.py) points at local Postgres; Railway injects `DATABASE_URL` in production.

### Frontend (`frontend/`)

- **React 18.3.1** + **react-dom 18.3.1**
- **Vite 6.4.3** + **@vitejs/plugin-react 5.2.0** — dev server and build tool ([frontend/vite.config.js](frontend/vite.config.js)). Pinned below the latest major versions for compatibility with the installed Node.js version (20.11.0); Vite 8/rolldown requires Node 20.19+/22.12+.
- **ESLint 9** with `@eslint/js`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` ([frontend/eslint.config.js](frontend/eslint.config.js)). `react/prop-types` is disabled (no PropTypes/TypeScript in this project).
- No router or state management library — a small `src/api/` client wraps `fetch`, and component state is managed with React hooks. `VITE_API_URL` (see [frontend/.env.example](frontend/.env.example)) points at the backend.

## Project structure

Backend layers, each with a single responsibility:

- **`app/api/routes/`** — FastAPI routers (HTTP layer only). Parses/validates requests via schemas, calls services or repositories, and maps results/exceptions to HTTP responses. No business logic or direct DB queries. Includes `auth.py` (OAuth login/callback/me/logout) and `admin.py` (user approval).
- **`app/api/deps.py`** — auth dependencies: `get_current_user` (reads the `access_token` cookie, decodes the JWT, loads the `User`), `require_approved_user` (403 unless `status == approved`), `require_admin` (403 unless email is in `settings.admin_emails`).
- **`app/services/`** — business logic. `CoverLetterService` orchestrates resume resolution, role creation, the OpenAI call, and persistence; `resume_parser.py` extracts text from uploaded resume PDFs (`extract_resume_text`); `oauth_profile.py` normalizes Google/Microsoft profile responses into a common `ProviderProfile`. Knows nothing about HTTP or FastAPI.
- **`app/repositories/`** — data access layer. One repository per model (`ResumeRepository`, `RoleRepository`, `CoverLetterRepository`, `UserRepository`); each is the *only* code that runs SQLAlchemy queries against its model.
- **`app/models/`** — SQLAlchemy ORM models (`Resume`, `Role`, `CoverLetter`, `User`), all inheriting from `Base` in `app/db/base.py`. Imported in `backend/alembic/env.py` (`import app.models`) so they register with `Base.metadata` for autogenerate. `User.status` is a `UserStatus` enum (`pending`/`approved`/`rejected`, default `pending`). `Resume`, `Role`, and `CoverLetter` each have a `user_id` FK to `users.id` for per-user data isolation.
- **`app/schemas/`** — Pydantic models defining API request/response contracts (`ResumeCreate`/`ResumeRead`, `GenerateCoverLetterRequest`/`CoverLetterRead`, `CoverLetterBody`, `FitAnalysis`, `UserRead`/`CurrentUserRead`). `CoverLetterRead` has nullable `cover_letter`, `fit_analysis`, and `why_this_company` fields since any output can be skipped.
- **`app/db/`** — `base.py` (declarative `Base`), `session.py` (engine, `SessionLocal`, `get_db` FastAPI dependency).
- **`app/core/config.py`** — the single `Settings` object (pydantic-settings), loaded from `backend/.env`. This is the **only** place environment variables are read.
- **`app/core/oauth.py`** — Authlib `OAuth` client registry for `google`/`microsoft`, config-driven from `settings`.
- **`app/core/security.py`** — `create_access_token`/`decode_access_token` (JWT, pure functions, no FastAPI/DB).

### Frontend (`frontend/`)

- **`src/api/`** — `client.js` (shared `fetch` wrapper with `credentials: 'include'`: JSON, `FormData`, and `DELETE` requests via `get`/`post`/`postForm`/`del`, error handling; exports `API_URL`), `resumes.js` (`getResumes`, `uploadResume`), `coverLetters.js` (`generateCoverLetter`, `getCoverLetterHistory`, `deleteCoverLetter`), `auth.js` (`getCurrentUser`, `logout`), `admin.js` (`listUsers`, `approveUser`, `rejectUser`).
- **`src/components/`** — `GenerateForm.jsx` (3-step wizard: resume → job details + output checkboxes → result; shows `LoadingBar` while generating), `ResultView.jsx` (fit analysis always visible; tabs between Cover Letter / Why This Company when both generated; copy button on each output), `HistoryList.jsx` (past generations, expandable, each with a delete button; handles nullable cover letter/fit analysis/why this company), `LoadingBar.jsx` (animated progress bar shown during generation), `LoginPage.jsx` (OAuth provider buttons, plain links to `{API_URL}/api/auth/{provider}/login`), `PendingApproval.jsx` (shown while `status` is `pending`/`rejected`), `AdminPanel.jsx` (user list with status filter + approve/reject).
- **`src/App.jsx`** — on mount calls `getCurrentUser()`; renders `LoginPage` (logged out), `PendingApproval` (`pending`/`rejected`), or the tab navigation (`generate` / `history`, plus `admin` if `is_admin`) for `approved` users. Holds shared state (saved resumes list, history refresh trigger, current user).
- **`.env.example`** — `VITE_API_URL`, copied to `.env.local` (gitignored) for local dev.

## Architecture decisions

- **SQLAlchemy models vs. Pydantic schemas are kept separate.** Models (`app/models/`) describe how data is stored; schemas (`app/schemas/`) describe how data looks over the API. This lets the API contract evolve independently of the table structure (e.g. `CoverLetterRead` decomposes the `cover_letter`/`fit_analysis` JSON columns into typed `CoverLetterBody`/`FitAnalysis` schemas) and prevents accidentally leaking ORM internals (relationships, lazy-loaded attributes) over the wire.

- **Business logic lives in `app/services/`, not in routes.** Routes ([backend/app/api/routes/cover_letter.py](backend/app/api/routes/cover_letter.py)) are thin: they validate input via schemas, delegate to a service, and translate exceptions to HTTP status codes. `CoverLetterService` ([backend/app/services/generator.py](backend/app/services/generator.py)) contains the actual orchestration (resolve resume → create role → call OpenAI → persist). This keeps the logic testable without spinning up FastAPI, and reusable if a second entry point (CLI, background job) is ever added.

- **Database queries are isolated in `app/repositories/`.** Services depend on repository classes (`ResumeRepository`, `RoleRepository`, `CoverLetterRepository`) rather than calling `db.query(...)` directly. Each repository is the single place that knows the query shape for its model, making it easy to change storage details (e.g. add caching, change ordering, swap ORM calls) without touching business logic.

- **`generate_cover_letter()` and `generate_why_this_company()` are pure functions, separate from `CoverLetterService`.** Each takes plain strings and calls OpenAI with no DB session — straightforward to unit test and mock. `generate_cover_letter` uses JSON mode; `generate_why_this_company` uses a plain-text system prompt.

- **Auth is cookie-based, not header-based.** OAuth login sets an httpOnly `access_token` JWT cookie (see `_cookie_kwargs()` in [backend/app/api/routes/auth.py](backend/app/api/routes/auth.py): `SameSite=Lax`/`Secure=False` in development, `SameSite=None`/`Secure=True` in production for the cross-site Netlify↔Railway setup). The frontend never reads or stores the token — every `fetch` call uses `credentials: 'include'` ([frontend/src/api/client.js](frontend/src/api/client.js)).

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
- Passwords must never be stored or returned in plain text. No password-based auth exists — login is OAuth-only (Google/Microsoft), and `User` stores no credential material.
- API responses must never expose internal-only fields (e.g. `hashed_password`, internal security IDs) or raw error stack traces in production. Note: [backend/app/api/routes/cover_letter.py](backend/app/api/routes/cover_letter.py) currently returns `str(e)` from a bare `except Exception` as a 500 detail — this should be replaced with a generic message plus server-side logging before production use. `UserRead`/`CurrentUserRead` deliberately omit `provider_user_id`.
- Always use the SQLAlchemy ORM (as the repositories already do) — never build raw SQL strings with interpolated user input.

## Environment variables

Defined in [backend/app/core/config.py](backend/app/core/config.py) (`Settings`), loaded from `backend/.env`:

| Variable | Used for | In `.env.example`? |
|---|---|---|
| `OPENAI_API_KEY` | Authenticates calls to the OpenAI API in `generate_cover_letter()` | Yes — currently `your-key-here` |
| `OPENAI_MODEL` | Model used for cover letter generation (default `gpt-4o`) | Yes — currently `gpt-4o` |
| `DATABASE_URL` | SQLAlchemy connection string for Postgres (default local Postgres; Railway sets this in production) | Yes — currently a local Postgres URL |
| `ENVIRONMENT` | `"development"` or `"production"` — controls the `access_token` cookie's `Secure`/`SameSite` attributes | Yes — `development` |
| `FRONTEND_URL` | Where OAuth callbacks redirect after login/logout | Yes — `http://localhost:5173` |
| `JWT_SECRET` | Signs/verifies the `access_token` cookie ([backend/app/core/security.py](backend/app/core/security.py)) | Yes — blank placeholder |
| `JWT_ALGORITHM` | JWT signing algorithm (default `HS256`) | Yes — `HS256` |
| `JWT_EXPIRE_MINUTES` | Access token lifetime in minutes (default 10080 = 7 days) | Yes — `10080` |
| `OAUTH_SESSION_SECRET` | Secret key for Authlib/Starlette's `SessionMiddleware` (OAuth state/nonce) | Yes — blank placeholder |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth app credentials | Yes — blank placeholders |
| `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth app credentials | Yes — blank placeholders |
| `MICROSOFT_TENANT` | Microsoft Entra tenant for OIDC discovery (default `common`) | Yes — `common` |
| `ADMIN_EMAILS` | JSON array of emails allowed to access `/api/admin/*` and the Admin tab | Yes — `["aparnaanand@outlook.com"]` |

[backend/.env.example](backend/.env.example) provides sensible non-secret defaults for `OPENAI_MODEL`, `DATABASE_URL`, `ENVIRONMENT`, `FRONTEND_URL`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `MICROSOFT_TENANT`, and `ADMIN_EMAILS`. `OPENAI_API_KEY`, `JWT_SECRET`, `OAUTH_SESSION_SECRET`, and all OAuth client ids/secrets are left blank/placeholder — keep it this way; generate real values locally with `openssl rand -hex 32` and never commit them.

CORS origins (`Settings.cors_origins`) are currently hardcoded in `config.py` rather than environment-driven (`http://localhost:5173` for Vite dev, plus the production Netlify URL — see Deployment below).

## Deployment

- **Frontend**: Netlify — https://jobsearch-ai.netlify.app (deploys from `main`, base directory `frontend`, build command `npm run build`, publish directory `dist`, env var `VITE_API_URL` set to the Railway backend URL)
- **Backend**: Railway — https://jobsearch-ai-production.up.railway.app (root directory `backend`, env vars `OPENAI_API_KEY`, `OPENAI_MODEL`, `DATABASE_URL`, plus the auth vars in the table above with `ENVIRONMENT=production`; `DATABASE_URL` is a reference to the linked Railway Postgres service)
- **Database**: Railway Postgres (production — separate from the local docker-compose Postgres used in development)
- **Migrations**: after schema changes, run `alembic upgrade head` against production via the Railway service's Console tab (this does not happen automatically)
- **OAuth redirect URIs**: each provider's app must allow `https://jobsearch-ai-production.up.railway.app/api/auth/{provider}/callback` (and `http://localhost:8000/api/auth/{provider}/callback` for local dev).

## What not to do

- Do not put business logic in route handlers — it belongs in `app/services/`.
- Do not put database queries in services — they belong in `app/repositories/`.
- Do not import or call `os.environ`/`os.getenv` directly — use `settings` from `app/core/config.py`.
- Do not expose internal error details (stack traces, raw exception strings) in API responses.
- Do not commit `.env`, `venv/`, `__pycache__/`, `node_modules/`, or `dist/` (already covered by [.gitignore](.gitignore)).
- Do not bypass `require_approved_user` or `require_admin` on resume/cover-letter/admin routes, and do not add new endpoints that read user identity from anything other than `app/api/deps.py` (e.g. a header or query param) — the cookie-based JWT is the single source of truth for the current user.
