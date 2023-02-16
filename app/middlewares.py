import secure
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core import translation
from app.core.config import Environment, settings


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    secure_headers = secure.Secure(server=secure.Server())

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        self.secure_headers.framework.fastapi(response)
        return response


class LocaleMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        lang = request.headers.get("Accept-Language", settings.DEFAULT_LOCALE)
        if lang not in settings.LOCALES:
            lang = settings.DEFAULT_LOCALE
        translation.activate(lang)
        response = await call_next(request)
        response.headers["Content-Language"] = lang
        return response


def setup_middlewares(app: FastAPI) -> None:
    app.add_middleware(LocaleMiddleware)

    if settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if settings.ENVIRONMENT > Environment.test:
        app.add_middleware(GZipMiddleware)
        app.add_middleware(HTTPSRedirectMiddleware)
        app.add_middleware(SecureHeadersMiddleware)
        app.add_middleware(ProxyHeadersMiddleware)
