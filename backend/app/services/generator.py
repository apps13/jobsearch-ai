"""
Cover-letter generation business logic.

Two parts:
  * generate_cover_letter(...) — the pure OpenAI call (no DB), easy to mock in tests.
  * CoverLetterService       — orchestrates resume lookup, generation, and persistence
                               via the repository layer. Knows no HTTP.
"""

import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.cover_letter_repo import CoverLetterRepository
from app.repositories.resume_repo import ResumeRepository
from app.repositories.role_repo import RoleRepository
from app.schemas.cover_letter import GenerateCoverLetterRequest

SYSTEM_PROMPT = """You are an expert career coach and professional writer specializing in
tailored job application materials. Your cover letters are concise, confident, and specific —
they avoid generic filler phrases and always connect the candidate's real experience to the
role's actual requirements.

You always respond in valid JSON matching the schema provided. No markdown, no explanation —
just the raw JSON object."""


def build_user_prompt(resume_text: str, job_description: str) -> str:
    return f"""
Analyze the resume and job description below. Then generate a tailored cover letter.

RESUME:
{resume_text}

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
    resume_text: str,
    job_description: str,
    model: str | None = None,
) -> dict:
    """Call OpenAI and return a dict with 'cover_letter' and 'fit_analysis' keys."""
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model=model or settings.openai_model,
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(resume_text, job_description)},
        ],
    )
    return json.loads(response.choices[0].message.content)


def generate_why_this_company(
    resume_text: str,
    job_description: str,
    model: str | None = None,
) -> str:
    """Call OpenAI and return a short 'Why this company?' paragraph."""
    client = OpenAI(api_key=settings.openai_api_key)

    prompt = (
        "Given the following resume and job description, write a 2–4 sentence first-person "
        "answer to the interview/application question 'Why do you want to work here?' or "
        "'Why this company?'. Be specific to the company and role — reference concrete details "
        "from the job description such as their mission, product, team focus, or values. "
        "Connect those details to relevant experience, skills, or goals from the resume. "
        "Avoid generic filler. Write in a natural, confident tone. "
        "Return only the paragraph — no heading, no extra text.\n\n"
        f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{job_description}"
    )

    response = client.chat.completions.create(
        model=model or settings.openai_model,
        max_tokens=300,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


class CoverLetterService:
    """Orchestrates the full generate-and-persist flow over the repositories."""

    def __init__(self, db: Session):
        self.resumes = ResumeRepository(db)
        self.roles = RoleRepository(db)
        self.cover_letters = CoverLetterRepository(db)

    def generate(self, req: GenerateCoverLetterRequest, user_id: int):
        resume_text = self._resolve_resume_text(req, user_id)
        role = self.roles.create(
            title=req.role_title, job_description=req.job_description, user_id=user_id
        )

        cover_letter_data = None
        fit_analysis_data = None
        if req.generate_cover_letter:
            result = generate_cover_letter(resume_text, req.job_description)
            cover_letter_data = result["cover_letter"]
            fit_analysis_data = result["fit_analysis"]

        wtc = None
        if req.generate_why_this_company:
            wtc = generate_why_this_company(resume_text, req.job_description)

        return self.cover_letters.create(
            role_id=role.id,
            user_id=user_id,
            cover_letter=cover_letter_data,
            fit_analysis=fit_analysis_data,
            why_this_company=wtc,
            resume_id=req.resume_id,
        )

    def history(self, user_id: int):
        return self.cover_letters.list(user_id)

    def delete_history_entry(self, cover_letter_id: int, user_id: int) -> bool:
        record = self.cover_letters.get(cover_letter_id, user_id)
        if record is None:
            return False
        role_id = record.role_id
        self.cover_letters.delete(cover_letter_id, user_id)
        self.roles.delete(role_id)
        return True

    def _resolve_resume_text(self, req: GenerateCoverLetterRequest, user_id: int) -> str:
        """Use a saved resume if an id is given, otherwise the pasted text."""
        if req.resume_id is not None:
            resume = self.resumes.get(req.resume_id, user_id)
            if resume is None:
                raise ValueError(f"Resume {req.resume_id} not found")
            return resume.content
        if req.resume_text:
            return req.resume_text
        raise ValueError("Provide either resume_id or resume_text")
