import pytest
import jwt
from fastapi import HTTPException
from app.core.config import settings
from app.core.dependencies import get_current_admin
from app.core.security import create_access_token, create_refresh_token

@pytest.mark.asyncio
async def test_get_current_admin_valid():
    token = create_access_token(subject="admin")
    sub = await get_current_admin(token=token)
    assert sub == "admin"

@pytest.mark.asyncio
async def test_get_current_admin_invalid_token_type():
    token = create_refresh_token(subject="admin")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(token=token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_admin_missing_sub():
    token = jwt.encode(
        {"type": "access"},
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(token=token)
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_admin_corrupted_token():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(token="invalid.token.str")
    assert exc_info.value.status_code == 401
