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
        return await self.session.get(Source, source_id)

    async def get_by_url(self, url: str) -> Source | None:
        """Fetch a source by its unique URL."""
        stmt = select(Source).where(Source.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: bool | None = None
    ) -> Sequence[Source]:
        """Fetch a paginated list of sources, optionally filtered by active status."""
        stmt = select(Source)
        
        # Динамическое построение запроса: добавляем фильтр только если параметр передан
        if is_active is not None:
            stmt = stmt.where(Source.is_active == is_active)
            
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, schema: SourceCreate) -> Source:
        """Create a new source record."""
        db_obj = Source(**schema.model_dump())
        self.session.add(db_obj)
        await self.session.commit()
        
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Source, schema: SourceUpdate) -> Source:
        """Update an existing source record."""
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