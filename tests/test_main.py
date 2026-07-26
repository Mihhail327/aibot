import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from app.api.deps import get_db_session, get_post_service
from app.core.exceptions import NotFoundException
from app.domains.posts.service import PostService

@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

@pytest.mark.asyncio
async def test_custom_api_exception_handler(async_client: AsyncClient, auth_headers: dict[str, str]):
    # Requesting non-existent source triggers NotFoundException (subclass of BaseAPIException)
    response = await async_client.get("/api/v1/sources/999999", headers=auth_headers)
    assert response.status_code == 404
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_cors_middleware_headers(async_client: AsyncClient):
    response = await async_client.get(
        "/health",
        headers={
            "Origin": "http://localhost",
        }
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_deps_get_db_session(mocker):
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.close = AsyncMock()

    mock_maker = MagicMock()
    mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("app.api.deps.async_session_maker", mock_maker)

    sessions = []
    async for s in get_db_session():
        sessions.append(s)

    assert len(sessions) == 1
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_deps_get_db_session_rollback_on_error(mocker):
    mock_session = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    mock_maker = MagicMock()
    mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("app.api.deps.async_session_maker", mock_maker)

    gen = get_db_session()
    await gen.__anext__()
    with pytest.raises(RuntimeError):
        await gen.athrow(RuntimeError("Database transaction failed"))

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()

def test_deps_get_post_service():
    mock_session = MagicMock()
    service = get_post_service(session=mock_session)
    assert isinstance(service, PostService)
