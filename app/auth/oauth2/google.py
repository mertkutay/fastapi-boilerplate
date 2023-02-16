from typing import Any

import aiohttp

from app.auth.oauth2.base import BaseOAuth2
from app.auth.oauth2.exceptions import OAuth2Exception
from app.core.config import settings


class GoogleOAuth2(BaseOAuth2):
    name = "google"
    client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
    redirect_uri = settings.CLIENT_URL + "/google-callback"
    authorize_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    access_token_endpoint = "https://oauth2.googleapis.com/token"  # noqa
    revoke_token_endpoint = "https://accounts.google.com/o/oauth2/revoke"  # noqa
    base_scopes = [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    @classmethod
    async def get_id_email(cls, token: str) -> tuple[str, str | None]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://people.googleapis.com/v1/people/me",
                params={"personFields": "emailAddresses"},
                headers={**cls.request_headers, "Authorization": f"Bearer {token}"},
            ) as response:
                if not response.ok:
                    raise OAuth2Exception.id_email_error

                data: dict[str, Any] = await response.json()

                user_id = data["resourceName"]
                user_email = next(
                    email["value"]
                    for email in data["emailAddresses"]
                    if email["metadata"]["primary"]
                )

                return user_id, user_email
