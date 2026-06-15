"""Auth routes — OAuth login/callback, current user, logout."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, get_current_user
from app.core.config import settings
from app.core.oauth import oauth
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import CurrentUserRead
from app.services.oauth_profile import normalize_profile

router = APIRouter(prefix="/api/auth", tags=["auth"])

PROVIDERS = {"google", "microsoft"}


def _cookie_kwargs() -> dict:
    if settings.environment == "production":
        return {"secure": True, "samesite": "none"}
    return {"secure": False, "samesite": "lax"}


@router.get("/{provider}/login")
async def login(provider: str, request: Request):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")
    client = oauth.create_client(provider)
    base_url = request.base_url
    if settings.environment == "production":
        base_url = base_url.replace(scheme="https")
    redirect_uri = f"{base_url}api/auth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def callback(provider: str, request: Request, db: Session = Depends(get_db)):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")

    client = oauth.create_client(provider)
    if provider == "microsoft":
        # The "common" tenant's discovery document advertises a templated
        # issuer (https://login.microsoftonline.com/{tenantid}/v2.0), which
        # never matches the tenant-specific `iss` in the actual id_token.
        token = await client.authorize_access_token(
            request, claims_options={"iss": {"essential": False}}
        )
    else:
        token = await client.authorize_access_token(request)
    profile = await normalize_profile(provider, client, token)

    user = UserRepository(db).upsert_from_oauth(
        email=profile.email,
        name=profile.name,
        picture=profile.picture,
        provider=provider,
        provider_user_id=profile.provider_user_id,
    )

    access_token = create_access_token(user.id, user.email)

    response = RedirectResponse(settings.frontend_url)
    response.set_cookie(
        COOKIE_NAME,
        access_token,
        httponly=True,
        max_age=settings.jwt_expire_minutes * 60,
        **_cookie_kwargs(),
    )
    return response


@router.get("/me", response_model=CurrentUserRead)
def me(user: User = Depends(get_current_user)):
    is_admin = user.email.lower() in {e.lower() for e in settings.admin_emails}
    return CurrentUserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        provider=user.provider,
        status=user.status,
        created_at=user.created_at,
        is_admin=is_admin,
    )


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, **_cookie_kwargs())
