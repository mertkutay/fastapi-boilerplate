from datetime import timedelta
from enum import IntEnum
from pathlib import Path

from pydantic import AnyHttpUrl, AnyUrl, BaseSettings, EmailStr, RedisDsn, validator


class Environment(IntEnum):
    local = 0
    test = 1
    dev = 2
    staging = 3
    production = 4


class Settings(BaseSettings):
    ENVIRONMENT: Environment

    @validator("ENVIRONMENT", pre=True)
    def get_environment(cls, v: str) -> Environment:
        return getattr(Environment, v)

    PROJECT_NAME: str
    SECRET_KEY: str
    ALLOWED_HOSTS: list[str] = []
    CORS_ORIGINS: list[AnyHttpUrl] = []
    SERVER_URL: AnyHttpUrl
    CLIENT_URL: AnyHttpUrl
    API_PATH: str = "/api/v1"

    LOCALES = ["en", "tr"]
    DEFAULT_LOCALE = "en"

    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URI(self) -> str:
        return AnyUrl.build(
            scheme="asyncpg",
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=f"/{self.POSTGRES_DB}",
        )

    CACHE_URI: RedisDsn

    ACCESS_TOKEN_EXPIRE: timedelta = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRE: timedelta = timedelta(days=30)
    EMAIL_VERIFICATION_TOKEN_EXPIRE: timedelta = timedelta(days=2)
    PASSWORD_RESET_TOKEN_EXPIRE: timedelta = timedelta(days=2)
    OAUTH2_STATE_TOKEN_EXPIRE: timedelta = timedelta(hours=1)

    GOOGLE_OAUTH2_CLIENT_ID: str = ""
    GOOGLE_OAUTH2_CLIENT_SECRET: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 0
    SMTP_TLS: bool = False
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    EMAIL_FROM: tuple[str, EmailStr] | None

    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    SENTRY_DSN: str = ""
    GEOIP_PATH: Path = Path("data/geoip")
    GEOIP_LICENSE: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()  # type: ignore


if settings.ENVIRONMENT == Environment.test:
    settings.POSTGRES_DB = "test"


TORTOISE_CONFIG = {
    "connections": {"default": settings.DATABASE_URI},
    "apps": {
        "models": {
            "models": [
                "aerich.models",
                "app.auth.models",
            ],
            "default_connection": "default",
        },
    },
}
