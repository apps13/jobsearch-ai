# JobSearch AI

A tool that generates tailored job application materials from your resume and a job description, using OpenAI.

**Live at:** https://jobsearch-ai.netlify.app

---

## What it does

Sign in with Google or Microsoft, then:

1. **Upload or select a resume** — upload a PDF (extracted and saved) or pick a previously saved one
2. **Paste a job description** — add the role title and full JD
3. **Choose your outputs** — generate any combination of:
   - **Cover Letter** — a tailored, structured cover letter connecting your experience to the role
   - **Why This Company** — a 2–4 sentence first-person answer to "Why do you want to work here?", specific to the company and role
4. **Review results** — fit analysis (match score, matched skills, gaps, recommendation) always shown; Cover Letter and Why This Company in tabs if both were generated, with a copy button on each
5. **Browse history** — past generations saved to your account; expand any entry or delete it

All data is private to your account — other users cannot see your resumes or history.

---

## Access

New accounts start as **pending** and require admin approval before generating. Contact the admin (`aparnaanand@outlook.com`) to request access.

---

## Local development

**Prerequisites:** Docker Desktop, Python 3.12, Node.js 20.11

```bash
# 1. Start local Postgres
docker compose up -d

# 2. Backend
cd backend
cp .env.example .env        # fill in secrets (see .env.example comments)
.\venv\Scripts\activate     # Windows; use source venv/bin/activate on Mac/Linux
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend (separate terminal)
cd frontend
cp .env.example .env.local  # set VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

App runs at `http://localhost:5173`. Backend at `http://localhost:8000`.

For tech stack details, architecture decisions, environment variables, and deployment notes — see [CLAUDE.md](CLAUDE.md).
