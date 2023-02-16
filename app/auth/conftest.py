from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from app.auth import models
from app.auth.tests import factories
from app.main import app
from app.utils import security


@pytest.fixture
async def user() -> models.User:
    return await factories.UserFactory.create()


@pytest.fixture
async def auth_client(user: models.User) -> AsyncGenerator[AsyncClient, None]:
    access_token = security.create_access_token(user.id)

    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver/api/v1",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as c:
            yield c
