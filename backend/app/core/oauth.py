"""OAuth client registry — Google and Microsoft, config-driven from settings."""

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="microsoft",
    client_id=settings.microsoft_client_id,
    client_secret=settings.microsoft_client_secret,
    server_metadata_url=(
        f"https://login.microsoftonline.com/{settings.microsoft_tenant}/v2.0/"
        ".well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)
