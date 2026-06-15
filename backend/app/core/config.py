"""
Application configuration.

All settings are read from the environment (or a local .env file) in one place,
so no other module calls os.getenv directly. Import the singleton `settings`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Database — Railway injects DATABASE_URL in production.
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/jobsearch"

    # CORS — origins allowed to call the API.
    cors_origins: list[str] = [
        "http://localhost:5173",            # Vite dev server
        "https://jobsearch-ai.netlify.app", # production frontend
    ]

    # Environment — controls cookie Secure/SameSite behavior. Set to
    # "production" on Railway.
    environment: str = "development"

    # Frontend URL — where OAuth callbacks redirect after login.
    frontend_url: str = "http://localhost:5173"

    # Auth — JWT issued in an httpOnly cookie after a successful OAuth login.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    # Required by Authlib's Starlette OAuth client for state/nonce storage.
    oauth_session_secret: str = ""

    # OAuth provider credentials.
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_tenant: str = "common"

    # Emails allowed to access the admin panel.
    admin_emails: list[str] = ["aparnaanand@outlook.com"]


settings = Settings()
