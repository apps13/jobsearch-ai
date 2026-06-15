"""Resume routes — save and retrieve reusable resumes."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.resume_repo import ResumeRepository
from app.schemas.resume import ResumeCreate, ResumeRead
from app.services.resume_parser import extract_resume_text

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeRead, status_code=201)
def create_resume(data: ResumeCreate, db: Session = Depends(get_db)):
    repo = ResumeRepository(db)
    if repo.get_by_label(data.label) is not None:
        raise HTTPException(status_code=400, detail="A resume already exists with this name.")
    return repo.create(label=data.label, content=data.content)


@router.post("/upload", response_model=ResumeRead, status_code=201)
def upload_resume(
    label: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    repo = ResumeRepository(db)
    if repo.get_by_label(label) is not None:
        raise HTTPException(status_code=400, detail="A resume already exists with this name.")
    try:
        content = extract_resume_text(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return repo.create(label=label, content=content)


@router.get("", response_model=list[ResumeRead])
def list_resumes(db: Session = Depends(get_db)):
    return ResumeRepository(db).list()


@router.get("/{resume_id}", response_model=ResumeRead)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = ResumeRepository(db).get(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    repo = ResumeRepository(db)
    try:
        deleted = repo.delete(resume_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="This resume is used by saved cover letters and can't be deleted.",
        )
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")
