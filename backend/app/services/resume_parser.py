"""Resume file parsing — extracts plain text from an uploaded PDF resume."""

from io import BytesIO

from fastapi import UploadFile
from PyPDF2 import PdfReader


def extract_resume_text(file: UploadFile) -> str:
    """Read an uploaded PDF and return its concatenated text content.

    Raises ValueError if the file isn't a PDF or no text could be extracted
    (e.g. a scanned/image-only PDF).
    """
    is_pdf = file.content_type == "application/pdf" or (
        file.filename is not None and file.filename.lower().endswith(".pdf")
    )
    if not is_pdf:
        raise ValueError("Resume file must be a PDF")

    reader = PdfReader(BytesIO(file.file.read()))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if not text:
        raise ValueError("Could not extract any text from the PDF")

    return text
