from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def patch_background_tasks() -> None:
    def call_immediately(self: Any, func: Callable, *args: Any, **kwargs: Any) -> Any:
        func(*args, **kwargs)

    pytest.MonkeyPatch().setattr("fastapi.BackgroundTasks.add_task", call_immediately)


@pytest.fixture(scope="module", autouse=True)
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://testserver/api/v1") as c:
            yield c
