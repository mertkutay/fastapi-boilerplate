from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import unquote, urlencode

import aiohttp

from app.auth.oauth2.exceptions import OAuth2Exception


class BaseOAuth2(ABC):
    name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    authorize_endpoint: str
    access_token_endpoint: str
    refresh_token_endpoint: str | None
    revoke_token_endpoint: str | None
    base_scopes: list[str] | None
    request_headers: dict[str, str] = {
        "Accept": "application/json",
    }

    @classmethod
    def get_authorization_url(
        cls,
        state: str | None = None,
        scope: list[str] | None = None,
        extras_params: dict[str, str] | None = None,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": cls.client_id,
            "redirect_uri": cls.redirect_uri,
        }

        if state is not None:
            params["state"] = state

        _scope = scope or cls.base_scopes
        if _scope is not None:
            params["scope"] = " ".join(_scope)

        if extras_params is not None:
            params = {**params, **extras_params}  # type: ignore

        return f"{cls.authorize_endpoint}?{urlencode(params)}"

    @classmethod
    async def get_access_token(
        cls, code: str, code_verifier: str | None = None
    ) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": unquote(code),
            "redirect_uri": cls.redirect_uri,
            "client_id": cls.client_id,
            "client_secret": cls.client_secret,
        }

        if code_verifier:
            data.update({"code_verifier": code_verifier})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                cls.access_token_endpoint, data=data, headers=cls.request_headers
            ) as response:
                if not response.ok:
                    raise OAuth2Exception.access_token_error

                return await response.json()

    @classmethod
    async def refresh_token(cls, refresh_token: str) -> dict[str, Any]:
        if cls.refresh_token_endpoint is None:
            raise OAuth2Exception.refresh_token_not_supported

        data = (
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": cls.client_id,
                "client_secret": cls.client_secret,
            },
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                cls.refresh_token_endpoint, data=data, headers=cls.request_headers
            ) as response:
                if not response.ok:
                    raise OAuth2Exception.refresh_token_error

                return await response.json()

    @classmethod
    async def revoke_token(cls, token: str, token_type_hint: str | None = None) -> None:
        if cls.revoke_token_endpoint is None:
            raise OAuth2Exception.revoke_token_not_supported

        data = {"token": token}

        if token_type_hint is not None:
            data["token_type_hint"] = token_type_hint

        async with aiohttp.ClientSession() as session:
            async with session.post(
                cls.revoke_token_endpoint, data=data, headers=cls.request_headers
            ) as response:
                if not response.ok:
                    raise OAuth2Exception.revoke_token_error

    @classmethod
    @abstractmethod
    async def get_id_email(cls, token: str) -> tuple[str, str | None]:
        ...
