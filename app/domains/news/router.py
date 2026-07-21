import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.news.models import NewsItem
from app.domains.news.repository import NewsItemRepository
from app.domains.news.schemas import NewsItemCreate, NewsItemResponse, NewsItemUpdate
from app.domains.news.service import NewsItemService

# Изолированный роутер для домена новостей
router = APIRouter(prefix="/news", tags=["News"])


def get_news_service(session: AsyncSession = Depends(get_db)) -> NewsItemService:
    """
    Dependency Injection factory for NewsItemService.
    Instantiates the repository and service with the current request`s database session.
    """
    repository = NewsItemRepository(session)
    return NewsItemService(repository)

@router.post("/", response_model=NewsItemResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    schema: NewsItemCreate,
    service: NewsItemService = Depends(get_news_service),
) -> NewsItem:
    """Create a new parsed news item."""
    return await service.create_news_item(schema)

@router.get("/", response_model=list[NewsItemResponse], status_code=status.HTTP_200_OK)
async def get_news_list(
    skip: int = 0,
    limit: int = 100,
    service: NewsItemService = Depends(get_news_service),
) -> Sequence[NewsItem]:
    """Retrieve a paginated list of news items."""
    return await service.get_all_news(skip=skip, limit=limit)


@router.get("/{news_id}", response_model=NewsItemResponse, status_code=status.HTTP_200_OK)
async def get_news_by_id(
    news_id: uuid.UUID,
    service: NewsItemService = Depends(get_news_service),
) -> NewsItem:
    """Retrieve a specific news item by its UUID."""
    return await service.get_news_item(news_id)


@router.patch("/{news_id}", response_model=NewsItemResponse, status_code=status.HTTP_200_OK)
async def update_news(
    news_id: uuid.UUID,
    schema: NewsItemUpdate,
    service: NewsItemService = Depends(get_news_service),
) -> NewsItem:
    """Partially update a news item."""
    return await service.update_news_item(news_id, schema)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: uuid.UUID,
    service: NewsItemService = Depends(get_news_service),
) -> None:
    """Delete a news item and all its cascaded relationships (e.g., Posts)."""
    await service.delete_news_item(news_id)