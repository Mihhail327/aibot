import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession

from  app.domains.news.repository import NewsItemRepository
from app.domains.news.schemas import NewsItemCreate

@pytest.mark.asyncio
async def test_create_and_get_news(db_session: AsyncSession):
    """Test standart CRUD operations for NewsItemRepository."""
    repo = NewsItemRepository(db_session)

    # 1. Create
    schema = NewsItemCreate(
        id=uuid4(),
        title="Test News",
        url="https://test.com/1",
        summary="Summary text",
        source="test_source",
        published_at=datetime.now(UTC),
    )
    news_item = await repo.create(schema)
    assert news_item.title == "Test News"

    # 2. Get by URL
    fetched_item = await repo.get_by_url("https://test.com/1")
    assert fetched_item is not None
    assert fetched_item.id == news_item.id