from typing import Sequence

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.keywords.models import Keyword
from app.domains.keywords.repository import KeywordRepository
from app.domains.keywords.schemas import KeywordCreate, KeywordUpdate


class KeywordService:
    """Business logic layer for the Keyword domain."""

    def __init__(self, repository: KeywordRepository) -> None:
        # Инжектим репозиторий (Dependency Injection)
        self.repository = repository

    async def get_keyword(self, keyword_id: int) -> Keyword:
        """Fetch a single keyword by id, raising an exception if not found."""
        keyword = await self.repository.get_by_id(keyword_id)
        if not keyword:
            # Изолируем HTTP-логику и выбрасываем бизнес-исключение
            raise NotFoundException(detail=f"Ключевое слово с ID {keyword_id} не найдено.")
        return keyword
    
    async def get_all_keywords(self, skip: int = 0, limit: int = 100) -> Sequence[Keyword]:
        """Fetch a paginated list of keywords."""
        return await self.repository.get_all(skip=skip, limit=limit)
    
    async def create_keyword(self, schema: KeywordCreate) -> Keyword:
        """Create a new keyword with duplicate prevention."""
        # Нормализуем слово для проверки уникальности
        normalized_word = schema.word.lower()

        existing_keyword = await self.repository.get_by_word(normalized_word)
        if existing_keyword:
            raise DuplicateResourceException(
                detail=f"Ключевое слово '{normalized_word}' уже существует."
            )
        return await self.repository.create(schema)
    
    async def update_keyword(self, keyword_id: int, schema: KeywordUpdate) -> Keyword:
        """Update a keyword after verifying its existence and uniqueness."""
        # Используем собственный метод для проверки существование (DRY)
        keyword = await self.get_keyword(keyword_id)

        if schema.word:
            normalized_word = schema.word.lower()
            # Проверяем на дубликатыб только если слово реально изменилось
            if normalized_word != keyword.word:
                existing_keyword = await self.repository. get_by_word(normalized_word)
                if existing_keyword:
                    raise DuplicateResourceException(
                        detail=f"Ключевое слово '{normalized_word}' уже занято."
                    )
        return await self.repository.update(db_obj=keyword, schema=schema)
    
    async def delete_keyword(self, keyword_id: int) -> None:
        """Delete a keyword after veryfying its existence."""
        keyword = await self.get_keyword(keyword_id)
        await self.repository.delete(keyword)