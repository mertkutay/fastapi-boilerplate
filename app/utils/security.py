from datetime import timedelta
from uuid import uuid4

import arrow
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from passlib.context import CryptContext

from app.auth import models
from app.auth.exceptions import AuthException
from app.auth.schemas import AccessToken, RefreshAccessToken
from app.core.config import settings

ALGORITHM = "HS256"
PWD_CONTEXT = CryptContext(schemes=["argon2"])


async def authenticate(credentials: OAuth2PasswordRequestForm) -> models.User | None:
    user = await models.User.filter(email=credentials.username).first()
    if not user:
        hash_password(credentials.password)
        return None

    if not verify_password(credentials.password, user.password):
        return None

    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PWD_CONTEXT.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)


async def create_auth_tokens(user_id: int) -> RefreshAccessToken:
    return RefreshAccessToken(
        token_type="Bearer",  # noqa
        access_token=create_access_token(user_id),
        refresh_token=await create_refresh_token(user_id),
    )


async def refresh_access_token(refresh_token: str) -> AccessToken:
    user_id = await verify_refresh_token(refresh_token)
    return AccessToken(
        token_type="Bearer", access_token=create_access_token(user_id)  # noqa
    )


def create_access_token(user_id: int) -> str:
    return create_token(user_id, "access_token", settings.ACCESS_TOKEN_EXPIRE)


async def create_refresh_token(user_id: int) -> str:
    to_encode = {
        "exp": (arrow.now() + settings.REFRESH_TOKEN_EXPIRE).int_timestamp,
        "iat": arrow.now().int_timestamp,
        "aud": "refresh_token",
        "sub": str(user_id),
        "jti": uuid4().hex,
    }
    token = jwt.encode(to_encode.copy(), settings.SECRET_KEY, algorithm=ALGORITHM)

    await models.OutstandingToken.create(
        user_id=user_id,
        jti=to_encode["jti"],
        token=token,
        created_at=to_encode["iat"],
        expires_at=to_encode["exp"],
    )
    return token


def create_email_verification_token(email: str) -> str:
    return create_token(
        email, "email_verification", settings.EMAIL_VERIFICATION_TOKEN_EXPIRE
    )


def create_password_reset_token(user_id: int) -> str:
    return create_token(user_id, "password_reset", settings.PASSWORD_RESET_TOKEN_EXPIRE)


def create_oauth2_state_token(state: str) -> str:
    return create_token(state, "oauth2", settings.OAUTH2_STATE_TOKEN_EXPIRE)


def create_token(sub: str | int, aud: str, ttl: timedelta) -> str:
    data = {
        "sub": str(sub),
        "aud": aud,
        "exp": (arrow.now() + ttl).int_timestamp,
        "iat": arrow.now().int_timestamp,
    }

    return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> int:
    try:
        payload = validate_token(token, "access_token")
    except JWTClaimsError as e:
        raise AuthException.invalid_access_token from e
    except ExpiredSignatureError as e:
        raise AuthException.expired_access_token from e
    return int(payload["sub"])


async def verify_refresh_token(refresh_token: str) -> int:
    try:
        payload = validate_token(refresh_token, "refresh_token")
    except JWTClaimsError as e:
        raise AuthException.invalid_refresh_token from e
    except ExpiredSignatureError as e:
        raise AuthException.expired_refresh_token from e

    jti = payload.get("jti")
    if jti and await models.BlacklistedToken.exists(token__jti=jti):
        raise AuthException.expired_refresh_token

    return int(payload["sub"])


def verify_password_reset_token(token: str) -> int:
    try:
        payload = validate_token(token, "password_reset")
    except JWTClaimsError as e:
        raise AuthException.invalid_password_reset_token from e
    except ExpiredSignatureError as e:
        raise AuthException.expired_password_reset_token from e
    return int(payload["sub"])


def verify_email_verification_token(token: str) -> str:
    try:
        payload = validate_token(token, "email_verification")
    except JWTClaimsError as e:
        raise AuthException.invalid_email_verification_token from e
    except ExpiredSignatureError as e:
        raise AuthException.expired_email_verification_token from e
    return payload["sub"]


def verify_oauth2_state_token(token: str) -> str:
    try:
        payload = validate_token(token, "oauth2")
    except JWTClaimsError as e:
        raise AuthException.invalid_oauth2_token from e
    except ExpiredSignatureError as e:
        raise AuthException.expired_oauth2_token from e
    return payload["sub"]


def validate_token(token: str, audience: str) -> dict[str, str]:
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[ALGORITHM], audience=audience
    )


async def invalidate_all_refresh_tokens(user_id: int) -> None:
    tokens = await models.OutstandingToken.filter(user_id=user_id)
    for token in tokens:
        await models.BlacklistedToken.get_or_create(token=token)
