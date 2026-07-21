import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.news.models import NewsItem
from app.domains.news.schemas import NewsItemCreate, NewsItemUpdate


class NewsItemRepository:
    """Data Access Layer for the NewsItem domain."""

    def __init__(self, session: AsyncSession) -> None:
        # Инжектим активную сессию БД
        self.session = session

    async def get_by_id(self, news_id: uuid.UUID) -> NewsItem | None:
        """Fetch a news item by its UUID primary key."""
        # Оптимизированный поиск по Primary Key
        return await self.session.get(NewsItem, news_id)
    
    async def get_by_url(self, url: str) -> NewsItem | None:
        """Fetch a news item by its unique URL, if provided."""
        if not url:
            return None
        
        # Индексированный поиск для быстрой проверки дубликатов при парсинге
        stmt = select(NewsItem). where(NewsItem.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[NewsItem]:
        """Fetch a paginated list of parsed news items."""
        # Можно расширить фильтрами (например, order_by(NewsItem.published_at.desc()))
        stmt = select(NewsItem).order_by(NewsItem.published_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create(self, schema: NewsItemCreate) -> NewsItem:
        """Create a new news record from parsing workers."""
        # Транстлируем данные из DTO в SQLAlchemy модель
        # Если id не передан, SQLAlchemy/PostgreSQL сгенерирует его автоматически
        db_obj = NewsItem(**schema.model_dump(exclude_unset=True))
        self.session.add(db_obj)

        # Коммит и обновление для получения сгенерированных Timestamp и UUID
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def update(self, db_obj: NewsItem, schema: NewsItemUpdate) -> NewsItem:
        """Update an existing news record."""
        # Обновляем только переданные поля (Patch семетрика)
        update_data = schema.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def delete(self, db_obj: NewsItem) -> None:
        """Delete a news record. Will cascade to related Posts."""
        await self.session.delete(db_obj)
        await self.session.commit()