from app.core.config import settings
from app.core.exceptions import (
    BaseAPIException,
    NotFoundException,
    DuplicateResourceException,
    ExternalServiceException,
)

def test_settings_properties() -> None:
    assert "postgresql+psycopg://" in settings.SQLALCHEMY_DATABASE_URI
    assert settings.REDIS_CACHE_URL.startswith("redis://")
    assert settings.REDIS_CELERY_URL.startswith("redis://")

def test_custom_exceptions() -> None:
    exc = BaseAPIException(detail="Base error", status_code=400)
    assert exc.status_code == 400
    assert exc.detail == "Base error"

    not_found = NotFoundException(detail="Resource missing")
    assert not_found.status_code == 404
    assert not_found.detail == "Resource missing"

    duplicate = DuplicateResourceException(detail="Already exists")
    assert duplicate.status_code == 409
    assert duplicate.detail == "Already exists"

    ext_err = ExternalServiceException(detail="Gateway failed")
    assert ext_err.status_code == 502
    assert ext_err.detail == "Gateway failed"
