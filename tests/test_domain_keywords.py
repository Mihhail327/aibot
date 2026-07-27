import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.keywords.repository import KeywordRepository
from app.domains.keywords.schemas import KeywordCreate, KeywordUpdate
from app.domains.keywords.service import KeywordService

@pytest.mark.asyncio
async def test_keyword_repository_crud(db_session: AsyncSession) -> None:
    repo = KeywordRepository(db_session)
    
    # 1. Create
    kw = await repo.create(KeywordCreate(word="Artificial Intelligence"))
    assert kw.id is not None
    assert kw.word == "artificial intelligence"

    # 2. Get by ID & Get by Word
    fetched_by_id = await repo.get_by_id(kw.id)
    assert fetched_by_id is not None
    assert fetched_by_id.word == "artificial intelligence"

    fetched_by_word = await repo.get_by_word("artificial intelligence")
    assert fetched_by_word is not None
    assert fetched_by_word.id == kw.id

    # 3. Get all
    all_kws = await repo.get_all(skip=0, limit=10)
    assert len(all_kws) == 1

    # 4. Update
    updated = await repo.update(kw, KeywordUpdate(word="AI"))
    assert updated.word == "ai"

    # 5. Delete
    await repo.delete(updated)
    deleted = await repo.get_by_id(kw.id)
    assert deleted is None

@pytest.mark.asyncio
async def test_keyword_service_business_logic(db_session: AsyncSession) -> None:
    repo = KeywordRepository(db_session)
    service = KeywordService(repo)

    # 1. Create
    kw1 = await service.create_keyword(KeywordCreate(word="Python"))
    assert kw1.word == "python"

    # 2. Duplicate word check
    with pytest.raises(DuplicateResourceException):
        await service.create_keyword(KeywordCreate(word="Python"))

    # 3. Get missing keyword
    with pytest.raises(NotFoundException):
        await service.get_keyword(99999)

    # 4. Update duplicate check
    kw2 = await service.create_keyword(KeywordCreate(word="FastAPI"))
    with pytest.raises(DuplicateResourceException):
        await service.update_keyword(kw2.id, KeywordUpdate(word="Python"))

    # 5. Delete keyword
    await service.delete_keyword(kw1.id)
    with pytest.raises(NotFoundException):
        await service.get_keyword(kw1.id)

@pytest.mark.asyncio
async def test_keywords_api_endpoints(async_client: AsyncClient, auth_headers: dict[str, str]) -> None:
    # Create keyword
    create_resp = await async_client.post(
        "/api/v1/keywords/",
        json={"word": "Machine Learning"},
        headers=auth_headers
    )
    assert create_resp.status_code == 201
    kw_id = create_resp.json()["id"]
    assert create_resp.json()["word"] == "machine learning"

    # List keywords
    list_resp = await async_client.get("/api/v1/keywords/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Get single keyword
    get_resp = await async_client.get(f"/api/v1/keywords/{kw_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == kw_id

    # Update keyword
    patch_resp = await async_client.patch(
        f"/api/v1/keywords/{kw_id}",
        json={"word": "Deep Learning"},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["word"] == "deep learning"

    # Delete keyword
    del_resp = await async_client.delete(f"/api/v1/keywords/{kw_id}", headers=auth_headers)
    assert del_resp.status_code == 204
