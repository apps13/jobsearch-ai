"""Normalizes OAuth user profiles into a common shape across providers."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderProfile:
    email: str
    name: str
    picture: str | None
    provider_user_id: str


async def normalize_profile(provider: str, client: Any, token: dict) -> ProviderProfile:
    if provider in ("google", "microsoft"):
        userinfo = token["userinfo"]
        return ProviderProfile(
            email=userinfo["email"],
            name=userinfo.get("name", ""),
            picture=userinfo.get("picture"),
            provider_user_id=userinfo["sub"],
        )

    raise ValueError(f"Unknown provider: {provider}")
