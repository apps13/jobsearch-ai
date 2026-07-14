"""
Cover-letter generation business logic.

Two parts:
  * generate_cover_letter(...) — the pure OpenAI call (no DB), easy to mock in tests.
  * CoverLetterService       — orchestrates resume lookup, generation, and persistence
                               via the repository layer. Knows no HTTP.

RAG integration (added):
  CoverLetterService.generate() now runs a retrieval step before calling the
  LLM. Instead of sending the full resume, it retrieves the top-k bullets most
  semantically similar to the job description (via retriever.py) and passes
  only those to the model. This reduces prompt size, improves specificity, and
  avoids diluting the model's attention with irrelevant resume sections.
"""

import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.cover_letter_repo import CoverLetterRepository
from app.repositories.resume_repo import ResumeRepository
from app.repositories.role_repo import RoleRepository
from app.schemas.cover_letter import GenerateCoverLetterRequest
from app.services.retriever import retrieve_relevant_bullets

# Injected as the system message on every chat completion call.
# Keeps the model in "JSON-only career coach" mode regardless of what the
# user prompt contains — prevents freeform prose or markdown bleeding in.
SYSTEM_PROMPT = """You are an expert career coach and professional writer specializing in
tailored job application materials. Your cover letters are concise, confident, and specific —
they avoid generic filler phrases and always connect the candidate's real experience to the
role's actual requirements.

You always respond in valid JSON matching the schema provided. No markdown, no explanation —
just the raw JSON object."""


def build_user_prompt(relevant_bullets: str, job_description: str) -> str:
    """
    Construct the user-turn message for cover letter generation.

    Args:
        relevant_bullets: Pre-filtered resume highlights — the top-k bullets
                          retrieved by the RAG pipeline, joined with bullet markers.
                          Labelled "RESUME HIGHLIGHTS" rather than "RESUME" to signal
                          to the model that this is a curated subset, not a full document.
        job_description:  The raw job posting text.

    Returns:
        A formatted string to send as the user message to the chat completion API.
    """
    return f"""
Analyze the resume highlights and job description below. Then generate a tailored cover letter.

RESUME HIGHLIGHTS:
{relevant_bullets}

JOB DESCRIPTION:
{job_description}

Respond with a JSON object matching this exact schema:
{{
  "cover_letter": {{
    "greeting": "string — e.g. 'To whom it may concern,' or a specific name if found in JD",
    "opening_paragraph": "string — hook that connects a specific achievement to the role",
    "body_paragraph_1": "string — 2-3 sentences on most relevant experience/skills",
    "body_paragraph_2": "string — 2-3 sentences on culture fit or a standout quality",
    "closing_paragraph": "string — confident call to action",
    "sign_off": "string — e.g. 'Thanks for your consideration,' or 'Best regards,'"
  }},
  "fit_analysis": {{
    "match_score": 85,
    "matched_skills": ["list of skills/experience found in both resume and JD"],
    "gaps": ["list of JD requirements not clearly evidenced in the resume"],
    "recommendation": "string — one sentence of honest advice"
  }}
}}

To compute "match_score": first list out the distinct requirements/skills mentioned in the
job description, then count how many of those are clearly evidenced in the resume. Compute
match_score = round(100 * matched_count / total_requirements). The result MUST be a whole
number between 0 and 100 — for example, meeting 8 out of 10 requirements gives a
match_score of 80, not 8. Do not divide your final answer by 10.
"""


def generate_cover_letter(
    relevant_bullets: str,
    job_description: str,
    model: str | None = None,
) -> dict:
    """
    Call the OpenAI Chat Completions API in JSON mode and return structured output.

    This is a pure function — no DB access, no side effects. Takes pre-retrieved
    resume highlights rather than the full resume text.

    Args:
        relevant_bullets: RAG-retrieved resume highlights (bullet-formatted string).
        job_description:  The full job posting text.
        model:            Override the model from settings (useful in tests).

    Returns:
        A dict with two keys: "cover_letter" (structured paragraphs) and
        "fit_analysis" (match score, matched skills, gaps, recommendation).
    """
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=model or settings.openai_model,
        max_tokens=1500,
        # JSON mode guarantees the response is valid JSON — no need to parse
        # markdown fences or handle malformed output defensively.
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(relevant_bullets, job_description)},
        ],
    )
    return json.loads(response.choices[0].message.content)


def generate_why_this_company(
    relevant_bullets: str,
    job_description: str,
    model: str | None = None,
) -> str:
    """
    Call the OpenAI Chat Completions API and return a plain-text "Why this company?" answer.

    Uses a plain-text (non-JSON-mode) completion because the output is a single
    prose paragraph, not structured data.

    Args:
        relevant_bullets: RAG-retrieved resume highlights (bullet-formatted string).
        job_description:  The full job posting text.
        model:            Override the model from settings (useful in tests).

    Returns:
        A 2–4 sentence first-person answer, stripped of leading/trailing whitespace.
    """
    client = OpenAI(api_key=settings.openai_api_key)

    prompt = (
        "Given the following resume highlights and job description, write a 2–4 sentence first-person "
        "answer to the interview/application question 'Why do you want to work here?' or "
        "'Why this company?'. Be specific to the company and role — reference concrete details "
        "from the job description such as their mission, product, team focus, or values. "
        "Connect those details to relevant experience, skills, or goals from the resume. "
        "Avoid generic filler. Write in a natural, confident tone. "
        "Return only the paragraph — no heading, no extra text.\n\n"
        f"RESUME HIGHLIGHTS:\n{relevant_bullets}\n\nJOB DESCRIPTION:\n{job_description}"
    )

    response = client.chat.completions.create(
        model=model or settings.openai_model,
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert career coach. Write concise, specific, genuine responses "
                    "tailored to the candidate and role. Return plain text only — no JSON, "
                    "no markdown, no headings, no extra formatting."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


class CoverLetterService:
    """
    Orchestrates the full generate-and-persist flow over the repositories.

    Knows nothing about HTTP — it accepts validated schema objects and returns
    ORM model instances. The route handler is responsible for mapping these to
    HTTP responses.
    """

    def __init__(self, db: Session):
        self.resumes = ResumeRepository(db)
        self.roles = RoleRepository(db)
        self.cover_letters = CoverLetterRepository(db)

    def generate(self, req: GenerateCoverLetterRequest, user_id: int):
        """
        Run the full pipeline: retrieve resume → RAG → generate → persist.

        Steps:
          1. Load resume text from DB (by id) or use the pasted text from the request.
          2. Run the RAG retrieval pipeline to get the most relevant resume bullets.
          3. Create a Role record (persists the job title and description for history).
          4. Call the generation function(s) selected in the request.
          5. Persist the results and return the CoverLetter ORM record.

        Args:
            req:     Validated request containing resume reference, job details,
                     and which outputs to generate.
            user_id: The authenticated user's database ID — used for data isolation
                     and the atomic generation counter in the repository.
        """
        # Step 1: Get raw resume text — from a saved resume or the request body.
        resume_text = self._resolve_resume_text(req, user_id)

        # Step 2: RAG retrieval — chunk the resume and find the top-k bullets
        # most semantically similar to the job description. Fall back to the full
        # resume text if chunking yields nothing (e.g. an unreadable PDF).
        bullets = retrieve_relevant_bullets(resume_text, req.job_description)
        relevant_bullets = "\n".join(f"• {b}" for b in bullets) if bullets else resume_text

        # Step 3: Persist the role before generation so it's available even if
        # the OpenAI call fails (role records are deleted with the cover letter).
        role = self.roles.create(
            title=req.role_title, job_description=req.job_description, user_id=user_id
        )

        # Steps 4a/4b: Call only the generation functions the user requested.
        # Both receive the same relevant_bullets string so retrieval runs once.
        cover_letter_data = None
        fit_analysis_data = None
        if req.generate_cover_letter:
            result = generate_cover_letter(relevant_bullets, req.job_description)
            cover_letter_data = result["cover_letter"]
            fit_analysis_data = result["fit_analysis"]

        wtc = None
        if req.generate_why_this_company:
            wtc = generate_why_this_company(relevant_bullets, req.job_description)

        # Step 5: Persist cover letter + atomically increment generations_used.
        return self.cover_letters.create(
            role_id=role.id,
            user_id=user_id,
            cover_letter=cover_letter_data,
            fit_analysis=fit_analysis_data,
            why_this_company=wtc,
            resume_id=req.resume_id,
        )

    def history(self, user_id: int):
        """Return all cover letters for *user_id*, ordered newest first."""
        return self.cover_letters.list(user_id)

    def delete_history_entry(self, cover_letter_id: int, user_id: int) -> bool:
        """
        Delete a cover letter and its associated Role record.

        Each generation creates exactly one Role, so deleting both is safe here.
        Returns False if the record doesn't exist or doesn't belong to *user_id*.
        """
        record = self.cover_letters.get(cover_letter_id, user_id)
        if record is None:
            return False
        role_id = record.role_id
        self.cover_letters.delete(cover_letter_id, user_id)
        self.roles.delete(role_id)
        return True

    def _resolve_resume_text(self, req: GenerateCoverLetterRequest, user_id: int) -> str:
        """
        Return the raw resume string from whichever source the request specifies.

        Prefers resume_id (a saved resume in the DB) over resume_text (pasted
        inline). Raises ValueError rather than returning None so the caller gets
        a clear error message rather than a confusing NoneType crash downstream.
        """
        if req.resume_id is not None:
            resume = self.resumes.get(req.resume_id, user_id)
            if resume is None:
                raise ValueError(f"Resume {req.resume_id} not found")
            return resume.content
        if req.resume_text:
            return req.resume_text
        raise ValueError("Provide either resume_id or resume_text")
