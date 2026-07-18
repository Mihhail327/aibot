from typing import Sequence

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.sources.models import Source
from app.domains.sources.repository import SourceRepository
from app.domains.sources.schemas import SourceCreate, SourceUpdate


class SourceService:
    """Business logic layer for the Source domain."""

    def __init__(self, repository: SourceRepository) -> None:
        # Инжектим репозиторий для работы с БД
        self.repository = repository

    async def get_source(self, source_id: int) -> Source:
        """Fetch a single source by ID, raising an exception if not found."""
        source = await self.repository.get_by_id(source_id)
        if not source:
            # Бизнес-правило: если ресурса нет, бросаем 404
            raise NotFoundException(detail=f"Источник с ID {source_id} не найден.")
        return source

    async def get_all_sources(self, skip: int = 0, limit: int = 100) -> Sequence[Source]:
        """Fetch a paginated list of sources."""
        # Прямой проброс к репозиторию, так как тут нет сложной логики
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create_source(self, schema: SourceCreate) -> Source:
        """Create a new source with duplication checks."""
        # Бизнес-правило: URL должен быть уникальным
        existing_source = await self.repository.get_by_url(schema.url)
        if existing_source:
            raise DuplicateResourceException(
                detail=f"Источник с URL '{schema.url}' уже существует."
            )
        
        return await self.repository.create(schema)

    async def update_source(self, source_id: int, schema: SourceUpdate) -> Source:
        """Update a source after verifying its existence."""
        # Сначала проверяем, существует ли источник (вызовет 404, если нет)
        source = await self.get_source(source_id)
        
        # Если клиент пытается обновить URL, проверяем, не занят ли он другим источником
        if schema.url and schema.url != source.url:
            existing_source = await self.repository.get_by_url(schema.url)
            if existing_source:
                raise DuplicateResourceException(
                    detail=f"URL '{schema.url}' уже занят другим источником."
                )

        return await self.repository.update(db_obj=source, schema=schema)

    async def delete_source(self, source_id: int) -> None:
        """Delete a source after verifying its existence."""
        # Проверяем существование перед удалением
        source = await self.get_source(source_id)
        await self.repository.delete(source)