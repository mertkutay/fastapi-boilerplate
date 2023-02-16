from datetime import datetime

from pydantic import EmailStr

from app.core.schemas import BaseModel


class UserRead(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    is_verified: bool

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None


class UserUpdate(BaseModel):
    password: str | None
    full_name: str | None


class OutstandingTokenDB(BaseModel):
    user_id: int
    jti: str
    token: str
    created_at: datetime
    expires_at: datetime


class AccessToken(BaseModel):
    token_type: str
    access_token: str

    class Config:
        alias_generator = None


class RefreshAccessToken(AccessToken):
    refresh_token: str


class OAuth2Authorization(BaseModel):
    authorization_url: str
