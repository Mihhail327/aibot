from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.sources.models import Source
from app.domains.sources.schemas import SourceCreate, SourceUpdate


class SourceRepository:
    """Data Access Layer for the Source domain."""

    def __init__(self, session: AsyncSession) -> None:
        # Инжектим сессию базы данных при создании репозитория
        self.session = session

    async def get_by_id(self, source_id: int) -> Source | None:
        """Fetch a source by its primary key."""
        # Оптимизированный поиск по первичному ключу в Алхимии
        return await self.session.get(Source, source_id)

    async def get_by_url(self, url: str) -> Source | None:
        """Fetch a source by its unique URL."""
        # Запрос для слоя бизнес-логики, чтобы проверять дубликаты перед созданием
        stmt = select(Source).where(Source.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Source]:
        """Fetch a paginated list of sources."""
        # Получение списка с базовой пагинацией
        stmt = select(Source).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, schema: SourceCreate) -> Source:
        """Create a new source record."""
        # Конвертируем Pydantic DTO в словарь и передаем в модель ORM
        db_obj = Source(**schema.model_dump())
        self.session.add(db_obj)
        await self.session.commit()
        
        # Обновляем объект, чтобы подтянуть сгенерированные БД поля (id, created_at)
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Source, schema: SourceUpdate) -> Source:
        """Update an existing source record."""
        # exclude_unset=True гарантирует, что мы обновим только те поля, 
        # которые клиент реально передал в PATCH-запросе
        update_data = schema.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Source) -> None:
        """Delete a source record."""
        await self.session.delete(db_obj)
        await self.session.commit()