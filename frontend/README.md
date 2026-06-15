# JobSearch AI — Frontend

## Stack

- **React** + **Vite** — UI and dev/build tooling
- **Plain `fetch`** via a small API client in `src/api/` (`client.js`, `resumes.js`, `coverLetters.js`) — no router or state management library; component state is managed with React hooks
- Talks to the FastAPI backend at the URL configured by `VITE_API_URL`

## Setup

```
cp .env.example .env.local
npm install
npm run dev
```

Make sure the backend is running (Postgres via `docker compose up -d`, migrations via `alembic upgrade head`, then `uvicorn app.main:app --reload`) before using the app.

## Security recommendations

- `VITE_API_URL` (and any future `VITE_*` vars) belong in `.env.local`, which is gitignored. **Never commit `.env*` files with real values.**
- Vite exposes every `VITE_*` variable to the client bundle — never put secrets (API keys, tokens, credentials) in frontend env vars. The OpenAI API key and database credentials live only in `backend/.env` and are never used by the frontend.
- Resume PDFs are uploaded directly to the backend at `VITE_API_URL` — make sure this points at HTTPS in any non-local deployment.
- The client-side PDF file-type check is a UX convenience only, not a security control. The backend independently validates and parses uploaded files.
