import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.domains.auth.models import AdminSettings

def get_valid_invite_token() -> str:
    if settings.INVITE_TOKEN:
        return settings.INVITE_TOKEN.get_secret_value()
    import jwt
    return jwt.encode(
        {"type": "invite"},
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )

@pytest.mark.asyncio
async def test_auth_login_uninitialized_system_fails(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "anypassword"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_auth_setup_without_invite_token_fails(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/setup",
        json={"password": "NewSecretPassword123!", "invite_token": "invalid_token"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_auth_setup_and_login_success(async_client: AsyncClient) -> None:
    invite_tok = get_valid_invite_token()
    # 1. Setup master password with valid invite token
    setup_resp = await async_client.post(
        "/api/v1/auth/setup",
        json={"password": "NewSecretPassword123!", "invite_token": invite_tok}
    )
    assert setup_resp.status_code == 200
    assert setup_resp.json()["message"] == "Master password successfully set"

    # 2. Login with correct password
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "NewSecretPassword123!"}
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # 3. Update existing master password
    setup_update_resp = await async_client.post(
        "/api/v1/auth/setup",
        json={"password": "UpdatedPassword456!", "invite_token": invite_tok}
    )
    assert setup_update_resp.status_code == 200

    # 4. Login with updated password
    login_updated_resp = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "UpdatedPassword456!"}
    )
    assert login_updated_resp.status_code == 200

@pytest.mark.asyncio
async def test_auth_login_incorrect_password(async_client: AsyncClient, seeded_admin: AdminSettings) -> None:
    response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect master password"

@pytest.mark.asyncio
async def test_auth_refresh_token_success(async_client: AsyncClient) -> None:
    refresh_tok = create_refresh_token(subject="admin")
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_tok}
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

@pytest.mark.asyncio
async def test_auth_refresh_token_invalid_type(async_client: AsyncClient) -> None:
    access_tok = create_access_token(subject="admin")
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_tok}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"

@pytest.mark.asyncio
async def test_auth_refresh_token_corrupted(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "corrupted_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"
