import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import models, oauth2, schemas
from app.auth.deps import get_current_user
from app.auth.emails import send_password_reset_email, send_verification_email
from app.auth.exceptions import AuthException
from app.utils import security

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_in: schemas.UserCreate, background_tasks: BackgroundTasks
) -> schemas.RefreshAccessToken:
    user = await models.User.filter(email=user_in.email).first()
    if user:
        raise AuthException.email_already_exists

    user = await models.User.create(
        email=user_in.email,
        password=security.hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    tokens = await security.create_auth_tokens(user.id)
    background_tasks.add_task(send_verification_email, user)
    return tokens


@router.post("/login")
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
) -> schemas.RefreshAccessToken:
    user = await security.authenticate(credentials)
    if not user:
        raise AuthException.invalid_credentials

    tokens = await security.create_auth_tokens(user.id)
    return tokens


@router.post("/refresh")
async def refresh(refresh_token: str = Body(embed=True)) -> schemas.AccessToken:
    return await security.refresh_access_token(refresh_token)


@router.get("/me")
async def me_read(user: models.User = Depends(get_current_user)) -> schemas.UserRead:
    return schemas.UserRead.from_orm(user)


@router.patch("/me")
async def me_update(
    *,
    user: models.User = Depends(get_current_user),
    user_in: schemas.UserUpdate,
) -> schemas.UserRead:
    if user_in.password:
        user_in.password = security.hash_password(user_in.password)

    user.update_from_dict(user_in.dict(exclude_unset=True))
    await user.save()
    return schemas.UserRead.from_orm(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def me_delete(user: models.User = Depends(get_current_user)) -> None:
    await user.delete()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(*, email: str = Body(embed=True)) -> None:
    user = await models.User.filter(email=email).first()
    if user:
        send_password_reset_email(user)


@router.post("/reset-password")
async def reset_password(token: str = Body(...), password: str = Body(...)) -> None:
    user_id = security.verify_password_reset_token(token)
    user = await models.User.filter(id=user_id).first()
    if user:
        user.update_from_dict({"password": security.hash_password(password)})
        await user.save()


@router.post("/request-verification", status_code=status.HTTP_202_ACCEPTED)
async def request_verification(
    *, user: models.User = Depends(get_current_user)
) -> None:
    if not user.is_verified:
        send_verification_email(user)


@router.post("/verify")
async def verify(token: str = Body(embed=True)) -> None:
    email = security.verify_email_verification_token(token)
    user = await models.User.filter(email=email).first()
    if user and not user.is_verified:
        user.update_from_dict({"is_verified": True})
        await user.save()


@router.get("/google/authorize")
async def google_authorize(
    scopes: list[str] | None = Query(None), state: str = ""
) -> schemas.OAuth2Authorization:
    state = security.create_oauth2_state_token(state)
    url = oauth2.GoogleOAuth2.get_authorization_url(state, scopes)
    return schemas.OAuth2Authorization(authorization_url=url)


@router.get("/google/callback")
async def google_callback(
    code: str, state: str, code_verifier: str | None = None
) -> schemas.RefreshAccessToken:
    tokens = await oauth2.GoogleOAuth2.get_access_token(code, code_verifier)
    _, email = await oauth2.GoogleOAuth2.get_id_email(tokens["access_token"])
    security.verify_oauth2_state_token(state)

    user, _ = await models.User.get_or_create(
        email=email, defaults={"password": security.hash_password(str(uuid.uuid4()))}
    )
    return await security.create_auth_tokens(user.id)
