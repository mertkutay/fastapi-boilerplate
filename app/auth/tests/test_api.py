import pytest
from faker import Faker
from httpx import AsyncClient
from pytest_mock import MockerFixture
from starlette.datastructures import URL, QueryParams

from app.auth import models
from app.auth.exceptions import AuthException
from app.auth.oauth2.google import GoogleOAuth2
from app.auth.tests import factories
from app.core.exceptions import ApiException
from app.utils import security
from app.utils.emails import EmailSender

pytestmark = pytest.mark.anyio

fake = Faker()


async def test_register(client: AsyncClient) -> None:
    email = fake.email()
    password = fake.password()
    full_name = fake.name()

    payload = {
        "email": email,
        "password": password,
        "fullName": full_name,
    }
    res = await client.post("/auth/register", json=payload)
    assert res.is_success

    data = res.json()
    assert data["access_token"] and data["refresh_token"]

    await security.verify_refresh_token(data["refresh_token"])
    await _test_access_token(data["access_token"], email)


async def test_register_email_exists(client: AsyncClient, user: models.User) -> None:
    password = fake.password()
    full_name = fake.name()

    payload = {
        "email": user.email,
        "password": password,
        "fullName": full_name,
    }
    res = await client.post("/auth/register", json=payload)

    assert ApiException.from_response(res) == AuthException.email_already_exists


async def test_login(client: AsyncClient) -> None:
    password = fake.password()

    user = await factories.UserFactory.create(password=password)

    payload = {
        "username": user.email,
        "password": password,
    }
    res = await client.post("/auth/login", data=payload)
    assert res.is_success

    data = res.json()
    assert data["access_token"] and data["refresh_token"]

    await security.verify_refresh_token(data["refresh_token"])
    await _test_access_token(data["access_token"], user.email)


async def test_login_invalid_creds(client: AsyncClient, user: models.User) -> None:
    payload = {
        "username": user.email,
        "password": fake.password(),
    }
    res = await client.post("/auth/login", data=payload)

    assert ApiException.from_response(res) == AuthException.invalid_credentials


async def test_refresh(client: AsyncClient, user: models.User) -> None:
    refresh_token = await security.create_refresh_token(user.id)

    payload = {
        "refresh_token": refresh_token,
    }
    res = await client.post("/auth/refresh", json=payload)
    assert res.is_success

    data = res.json()
    assert data["access_token"]
    await _test_access_token(data["access_token"], user.email)


async def _test_access_token(token: str, email: str) -> None:
    user_id = security.verify_access_token(token)
    user = await models.User.filter(email=email).first()
    assert user
    assert user.id == user_id


async def test_me_read(auth_client: AsyncClient, user: models.User) -> None:
    res = await auth_client.get("/auth/me")
    assert res.is_success

    data = res.json()
    assert data["email"] == user.email
    assert data["fullName"] == user.full_name


async def test_me_update(auth_client: AsyncClient, user: models.User) -> None:
    payload = {
        "full_name": "Another Test Name",
        "password": fake.password(),
    }
    res = await auth_client.patch("/auth/me", json=payload)
    assert res.is_success

    data = res.json()
    assert data["fullName"] == payload["full_name"]

    await user.refresh_from_db()
    assert user.full_name == payload["full_name"]
    assert security.verify_password(payload["password"], user.password)


async def test_me_delete(auth_client: AsyncClient, user: models.User) -> None:
    res = await auth_client.delete("/auth/me")
    assert res.is_success

    assert not await models.User.exists(email=user.email)


async def test_forgot_password(
    client: AsyncClient, user: models.User, mocker: MockerFixture
) -> None:
    spy = mocker.spy(EmailSender, "send_email")

    payload = {
        "email": user.email,
    }
    res = await client.post("/auth/forgot-password", json=payload)
    assert res.is_success

    spy.assert_called_once()
    assert spy.call_args[0][0] == [user.email]


async def test_reset_password(client: AsyncClient, user: models.User) -> None:
    token = security.create_password_reset_token(user.id)

    payload = {
        "token": token,
        "password": "newpassword123",
    }
    res = await client.post("/auth/reset-password", json=payload)
    assert res.is_success

    await user.refresh_from_db()
    assert security.verify_password(payload["password"], user.password)


async def test_request_verification(
    auth_client: AsyncClient, user: models.User, mocker: MockerFixture
) -> None:
    spy = mocker.spy(EmailSender, "send_email")

    res = await auth_client.post("/auth/request-verification")
    assert res.is_success

    spy.assert_called_once()
    assert spy.call_args[0][0] == [user.email]


async def test_verify(client: AsyncClient, user: models.User) -> None:
    token = security.create_email_verification_token(user.email)

    payload = {
        "token": token,
    }
    res = await client.post("/auth/verify", json=payload)
    assert res.is_success

    await user.refresh_from_db()
    assert user.is_verified


async def test_google_authorize(client: AsyncClient) -> None:
    state = "state"
    res = await client.get("/auth/google/authorize", params={"state": state})
    assert res.is_success

    data = res.json()
    assert data["authorizationUrl"]
    assert data["authorizationUrl"].startswith(GoogleOAuth2.authorize_endpoint)

    url = URL(data["authorizationUrl"])
    assert state == security.verify_oauth2_state_token(QueryParams(url.query)["state"])


async def test_google_callback(client: AsyncClient, mocker: MockerFixture) -> None:
    email = fake.email()

    mocker.patch(
        "app.auth.oauth2.GoogleOAuth2.get_access_token",
        autospec=True,
        return_value={"access_token": fake.password()},
    )
    mocker.patch(
        "app.auth.oauth2.GoogleOAuth2.get_id_email",
        autospec=True,
        return_value=("user_id", email),
    )

    state = "state"
    res = await client.get(
        "/auth/google/callback",
        params={
            "code": fake.password(),
            "state": security.create_oauth2_state_token(state),
            "code_verifier": "",
        },
    )
    assert res.is_success

    assert await models.User.exists(email=email)

    data = res.json()
    assert data["access_token"]
    await _test_access_token(data["access_token"], email)
