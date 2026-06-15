"""
Application entry point.

Thin app factory: builds the FastAPI app, configures CORS, and wires the routers.
All real work lives in the api / services / repositories layers.

Schema is managed via Alembic migrations (see backend/alembic/). Run
`alembic upgrade head` to apply migrations before starting the app.

Run locally:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import admin, auth, cover_letter, health, resume
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="JobSearch AI API",
        description="Generates tailored cover letters and fit analysis from a resume and job description.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.oauth_session_secret)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(resume.router)
    app.include_router(cover_letter.router)

    return app


app = create_app()
