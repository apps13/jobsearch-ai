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
        "https://jobsearch-ai.netlify.app", # production frontend — update to real domain
    ]


settings = Settings()
