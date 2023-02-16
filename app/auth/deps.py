from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.auth import models
from app.auth.exceptions import AuthException
from app.core.config import settings
from app.utils import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PATH}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> models.User:
    user_id = security.verify_access_token(token)
    user = await models.User.filter(id=user_id).first()
    if not user:
        raise AuthException.user_not_found
    if not user.is_active:
        raise AuthException.user_is_inactive
    return user


async def get_current_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_superuser:
        raise AuthException.user_not_superuser
    return current_user
