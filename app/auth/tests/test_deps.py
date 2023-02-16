import pytest
from faker import Faker

from app.auth import deps
from app.auth.exceptions import AuthException
from app.auth.tests import factories
from app.utils import security

pytestmark = pytest.mark.anyio

fake = Faker()


async def test_get_current_user() -> None:
    user = await factories.UserFactory.create()

    token = security.create_access_token(user.id)

    assert user == (await deps.get_current_user(token))


async def test_get_current_user_not_found() -> None:
    token = security.create_access_token(fake.pyint())

    with pytest.raises(AuthException) as exc_info:
        await deps.get_current_user(token)

    assert exc_info.value == AuthException.user_not_found


async def test_get_current_user_is_inactive() -> None:
    user = await factories.UserFactory.create(is_active=False)

    token = security.create_access_token(user.id)

    with pytest.raises(AuthException) as exc_info:
        await deps.get_current_user(token)

    assert exc_info.value == AuthException.user_is_inactive


async def test_get_current_superuser() -> None:
    user = await factories.UserFactory.create(is_superuser=True)

    token = security.create_access_token(user.id)

    assert user == (
        await deps.get_current_superuser(await deps.get_current_user(token))
    )


async def test_get_current_superuser_not() -> None:
    user = await factories.UserFactory.create(is_superuser=False)

    token = security.create_access_token(user.id)

    with pytest.raises(AuthException) as exc_info:
        assert user == (
            await deps.get_current_superuser(await deps.get_current_user(token))
        )

    assert exc_info.value == AuthException.user_not_superuser
