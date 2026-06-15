"""Health check route — used by Railway and monitoring to verify the server is up."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}
