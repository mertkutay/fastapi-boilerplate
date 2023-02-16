import sentry_sdk
from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse
from tortoise.contrib.fastapi import register_tortoise

from app.core.api import router
from app.core.config import TORTOISE_CONFIG, Environment, settings
from app.core.exceptions import setup_exception_handlers
from app.core.limiter import RateLimiter
from app.middlewares import setup_middlewares

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT.name,
        traces_sample_rate=0.0,
    )

global_dependencies = []
if settings.ENVIRONMENT > Environment.test:
    global_dependencies.append(Depends(RateLimiter(times=100, seconds=60)))

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
    dependencies=global_dependencies,
)


app.include_router(router)

setup_middlewares(app)

setup_exception_handlers(app)

register_tortoise(
    app,
    config=TORTOISE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)
