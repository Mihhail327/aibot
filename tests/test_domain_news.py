import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.news.repository import NewsItemRepository
from app.domains.news.schemas import NewsItemCreate, NewsItemUpdate
from app.domains.news.service import NewsItemService
from app.domains.news.tasks import parse_channels_task, _run_parsing_pipeline
from app.domains.sources.models import Source
from app.domains.keywords.models import Keyword

@pytest.mark.asyncio
async def test_news_repository_crud(db_session: AsyncSession):
    repo = NewsItemRepository(db_session)

    # 1. Create
    schema = NewsItemCreate(
        title="GPT-5 Released",
        url="https://openai.com/blog/gpt-5",
        summary="OpenAI announces GPT-5 model.",
        source="OpenAI Blog",
        published_at=datetime.now(timezone.utc),
        raw_text="Full announcement text..."
    )
    news = await repo.create(schema)
    assert news.id is not None
    assert news.title == "GPT-5 Released"
    assert news.url == "https://openai.com/blog/gpt-5"

    # 2. Get by ID & Get by URL
    fetched_by_id = await repo.get_by_id(news.id)
    assert fetched_by_id is not None
    assert fetched_by_id.title == news.title

    fetched_by_url = await repo.get_by_url(news.url)
    assert fetched_by_url is not None
    assert fetched_by_url.id == news.id

    assert await repo.get_by_url("") is None

    # 3. Get all
    all_news = await repo.get_all(skip=0, limit=10)
    assert len(all_news) == 1

    # 4. Update
    updated = await repo.update(news, NewsItemUpdate(title="GPT-5 Official Release"))
    assert updated.title == "GPT-5 Official Release"

    # 5. Delete
    await repo.delete(updated)
    assert await repo.get_by_id(news.id) is None

@pytest.mark.asyncio
async def test_news_service_business_logic(db_session: AsyncSession):
    repo = NewsItemRepository(db_session)
    service = NewsItemService(repo)

    now = datetime.now(timezone.utc)
    # 1. Create item
    news1 = await service.create_news_item(NewsItemCreate(
        title="AI Breakthrough",
        url="https://ai.org/news/1",
        summary="Summary text",
        source="AI Org",
        published_at=now
    ))
    assert news1.title == "AI Breakthrough"

    # 2. Duplicate URL check on create
    with pytest.raises(DuplicateResourceException):
        await service.create_news_item(NewsItemCreate(
            title="AI Breakthrough Copy",
            url="https://ai.org/news/1",
            summary="Summary text",
            source="AI Org",
            published_at=now
        ))

    # 3. Get missing item
    with pytest.raises(NotFoundException):
        await service.get_news_item(uuid.uuid4())

    # 4. Update item duplicate URL check
    news2 = await service.create_news_item(NewsItemCreate(
        title="AI News 2",
        url="https://ai.org/news/2",
        summary="Summary 2",
        source="AI Org",
        published_at=now
    ))
    with pytest.raises(DuplicateResourceException):
        await service.update_news_item(news2.id, NewsItemUpdate(url="https://ai.org/news/1"))

    # 5. Delete item
    await service.delete_news_item(news1.id)
    with pytest.raises(NotFoundException):
        await service.get_news_item(news1.id)

@pytest.mark.asyncio
async def test_news_api_endpoints(async_client: AsyncClient, auth_headers: dict[str, str]):
    payload = {
        "title": "Quantum Computing Milestone",
        "url": "https://tech.example/quantum",
        "summary": "Quantum supremacy achieved.",
        "source": "Tech News",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "raw_text": "Detailed quantum paper text..."
    }
    # Create
    create_resp = await async_client.post("/api/v1/news/", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    news_id = create_resp.json()["id"]

    # List
    list_resp = await async_client.get("/api/v1/news/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Get single
    get_resp = await async_client.get(f"/api/v1/news/{news_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == news_id

    # Update
    patch_resp = await async_client.patch(
        f"/api/v1/news/{news_id}",
        json={"title": "Quantum Computing Milestone 2026"},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Quantum Computing Milestone 2026"

    # Delete
    del_resp = await async_client.delete(f"/api/v1/news/{news_id}", headers=auth_headers)
    assert del_resp.status_code == 204

@pytest.mark.asyncio
async def test_run_parsing_pipeline(db_session: AsyncSession, mocker):
    # Seed a Telegram source and an RSS source
    tg_source = Source(name="TG Channel", url="https://t.me/testchannel", is_active=True, source_type="telegram")
    rss_source = Source(name="RSS Feed", url="https://feed.com/rss", is_active=True, source_type="rss")
    keyword = Keyword(word="AI")
    
    db_session.add_all([tg_source, rss_source, keyword])
    await db_session.commit()

    # Mock Telegram parser client & channel parser
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mocker.patch("app.domains.news.tasks.TelegramParserClient", return_value=mock_client_instance)

    mock_tg_msg = MagicMock()
    mock_tg_msg.id = 100
    mock_tg_msg.text = "AI revolution is happening now in technology"
    mock_tg_msg.date = datetime.now(timezone.utc)

    mock_tg_parser = MagicMock()
    mock_tg_parser.fetch_recent_messages = AsyncMock(return_value=[mock_tg_msg])
    mock_tg_parser.filter_by_keywords.return_value = [mock_tg_msg]
    mocker.patch("app.domains.news.tasks.TelegramChannelParser", return_value=mock_tg_parser)

    # Mock RSS parser
    mock_rss_item = MagicMock()
    mock_rss_item.title = "AI in Healthcare"
    mock_rss_item.url = "https://feed.com/rss/item1"
    mock_rss_item.summary = "Summary of AI in Healthcare"
    mock_rss_item.published_at = datetime.now(timezone.utc)

    mock_rss_parser = MagicMock()
    mock_rss_parser.fetch_feed = AsyncMock(return_value=[mock_rss_item])
    mocker.patch("app.domains.news.tasks.RSSParser", return_value=mock_rss_parser)

    # Mock session maker in tasks to use our db_session
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("app.domains.news.tasks.async_session_maker", return_value=mock_session_ctx)

    # Mock Celery delay call
    mock_delay = mocker.patch("app.domains.news.tasks.process_and_publish_post.delay")

    await _run_parsing_pipeline()

    assert mock_delay.call_count == 2

def test_parse_channels_task(mocker):
    mocker.patch("app.domains.news.tasks._run_parsing_pipeline", return_value=None)
    res = parse_channels_task()
    assert res == "Сбор новостей успешно завершен."
