import uuid
from typing import Sequence

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.news.models import NewsItem
from app.domains.news.repository import NewsItemRepository
from app.domains.news.schemas import NewsItemCreate, NewsItemUpdate


class NewsItemService:
    """Business logic layer for the NewsItem domain."""

    def __init__(self, repository: NewsItemRepository) -> None:
        # Внедрение зависимости (Dependency Injection) для изоляции доступа к БД
        self.repository = repository

    async def get_news_item(self, news_id: uuid.UUID) -> NewsItem:
        """Fetch a single news item by ID, raising an exception if not found."""
        item = await self.repository.get_by_id(news_id)
        if not item:
            # Превращаем технический None в бизнес-исключение
            raise NotFoundException(detail=f"Новость с ID {news_id} не найдена.")
        return item

    async def get_all_news(self, skip: int = 0, limit: int = 100) -> Sequence[NewsItem]:
        """Fetch a paginated list of news items."""
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create_news_item(self, schema: NewsItemCreate) -> NewsItem:
        """Create a new news item with idempotency and duplication checks."""
        # Проверяем уникальность только если парсер передал URL
        if schema.url:
            existing_item = await self.repository.get_by_url(schema.url)
            if existing_item:
                # Воркер или API контроллер должны перехватить эту ошибку
                raise DuplicateResourceException(
                    detail=f"Новость с URL '{schema.url}' уже существует."
                )
        
        return await self.repository.create(schema)

    async def update_news_item(self, news_id: uuid.UUID, schema: NewsItemUpdate) -> NewsItem:
        """Update a news item after verifying its existence and URL uniqueness."""
        # Убеждаемся, что целевая новость существует
        item = await self.get_news_item(news_id)
        
        # Если пытаемся изменить URL, проверяем конфликты с другими записями
        if schema.url and schema.url != item.url:
            existing_item = await self.repository.get_by_url(schema.url)
            if existing_item:
                raise DuplicateResourceException(
                    detail=f"URL '{schema.url}' уже занят другой новостью."
                )

        return await self.repository.update(db_obj=item, schema=schema)

    async def delete_news_item(self, news_id: uuid.UUID) -> None:
        """Delete a news item after verifying its existence."""
        item = await self.get_news_item(news_id)
        await self.repository.delete(item)