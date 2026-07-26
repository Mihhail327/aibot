import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.sources.models import Source
from app.domains.sources.repository import SourceRepository
from app.domains.sources.schemas import SourceCreate, SourceUpdate
from app.domains.sources.service import SourceService
from app.domains.sources.tasks import test_parsing_task

@pytest.mark.asyncio
async def test_source_repository_crud(db_session: AsyncSession):
    repo = SourceRepository(db_session)
    
    # 1. Create
    schema = SourceCreate(name="TechCrunch", url="https://techcrunch.com/feed", source_type="rss", is_active=True)
    source = await repo.create(schema)
    assert source.id is not None
    assert source.name == "TechCrunch"
    assert source.url == "https://techcrunch.com/feed"
    assert source.source_type == "rss"
    assert source.is_active is True

    # 2. Get by ID & Get by URL
    fetched_by_id = await repo.get_by_id(source.id)
    assert fetched_by_id is not None
    assert fetched_by_id.url == source.url

    fetched_by_url = await repo.get_by_url(source.url)
    assert fetched_by_url is not None
    assert fetched_by_url.id == source.id

    # 3. Get all with filters
    all_sources = await repo.get_all(skip=0, limit=10, is_active=True)
    assert len(all_sources) == 1

    inactive_sources = await repo.get_all(is_active=False)
    assert len(inactive_sources) == 0

    # 4. Update
    update_schema = SourceUpdate(name="TechCrunch Updated", is_active=False)
    updated = await repo.update(source, update_schema)
    assert updated.name == "TechCrunch Updated"
    assert updated.is_active is False

    # 5. Delete
    await repo.delete(updated)
    deleted = await repo.get_by_id(source.id)
    assert deleted is None

@pytest.mark.asyncio
async def test_source_service_business_logic(db_session: AsyncSession):
    repo = SourceRepository(db_session)
    service = SourceService(repo)

    # 1. Create
    source1 = await service.create_source(
        SourceCreate(name="TG News", url="@tg_news", source_type="telegram")
    )
    assert source1.name == "TG News"

    # 2. Duplicate URL check on create
    with pytest.raises(DuplicateResourceException):
        await service.create_source(
            SourceCreate(name="TG News Dup", url="@tg_news", source_type="telegram")
        )

    # 3. Get missing source
    with pytest.raises(NotFoundException):
        await service.get_source(99999)

    # 4. Update source & duplicate URL check
    source2 = await service.create_source(
        SourceCreate(name="TG News 2", url="@tg_news_2", source_type="telegram")
    )
    with pytest.raises(DuplicateResourceException):
        await service.update_source(
            source2.id, SourceUpdate(url="@tg_news")
        )

    # 5. Delete source
    await service.delete_source(source1.id)
    with pytest.raises(NotFoundException):
        await service.get_source(source1.id)

@pytest.mark.asyncio
async def test_sources_api_endpoints(async_client: AsyncClient, auth_headers: dict[str, str]):
    # Create source via API
    create_payload = {"name": "HackerNews", "url": "https://news.ycombinator.com/rss", "source_type": "rss"}
    response = await async_client.post("/api/v1/sources/", json=create_payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    source_id = data["id"]
    assert data["name"] == "HackerNews"

    # Get sources list
    list_resp = await async_client.get("/api/v1/sources/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Get single source
    get_resp = await async_client.get(f"/api/v1/sources/{source_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == source_id

    # Update source
    patch_resp = await async_client.patch(
        f"/api/v1/sources/{source_id}",
        json={"name": "HackerNews RSS", "is_active": False},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "HackerNews RSS"
    assert patch_resp.json()["is_active"] is False

    # Delete source
    del_resp = await async_client.delete(f"/api/v1/sources/{source_id}", headers=auth_headers)
    assert del_resp.status_code == 204

def test_source_task_execution(mocker):
    # Test Celery test_parsing_task
    res = test_parsing_task.apply(args=["https://example.com/rss"])
    assert res.result == {"status": "success", "url": "https://example.com/rss"}

def test_source_task_retry(mocker):
    mocker.patch("time.sleep", side_effect=ValueError("Parsing failed"))
    with pytest.raises(Exception) as exc:
        test_parsing_task.run("https://example.com/fail")
    assert "Parsing failed" in str(exc.value)



