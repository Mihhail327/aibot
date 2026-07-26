import pytest
import jwt
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_invite_token,
)

def test_password_hashing():
    password = "MySecurePassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_create_access_token():
    token = create_access_token(subject="admin")
    assert isinstance(token, str)
    
    payload = jwt.decode(
        token,
        settings.SECRET_KEY.get_secret_value(),
        algorithms=["HS256"]
    )
    assert payload["sub"] == "admin"
    assert payload["type"] == "access"
    assert "exp" in payload

def test_create_refresh_token():
    token = create_refresh_token(subject="admin")
    assert isinstance(token, str)
    
    payload = jwt.decode(
        token,
        settings.SECRET_KEY.get_secret_value(),
        algorithms=["HS256"]
    )
    assert payload["sub"] == "admin"
    assert payload["type"] == "refresh"
    assert "exp" in payload

def test_verify_invite_token():
    if settings.INVITE_TOKEN:
        assert verify_invite_token(settings.INVITE_TOKEN.get_secret_value()) is True

    invite_token = jwt.encode(
        {"type": "invite"},
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )
    assert verify_invite_token(invite_token) is True
    
    invalid_token = jwt.encode(
        {"type": "access"},
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )
    assert verify_invite_token(invalid_token) is False
    assert verify_invite_token("corrupted.token.string") is False
