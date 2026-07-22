from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.keywords.models import Keyword
from app.domains.keywords.schemas import KeywordCreate, KeywordUpdate


class KeywordRepository:
    """Data Access Layer for the Keyword domain."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, keyword_id: int) -> Keyword | None:
        """Fetch a keyword by its primary key."""
        return await self.session.get(Keyword, keyword_id)
    
    async def get_by_word(self, word: str) -> Keyword | None:
        """Fetch a keyword by its unique string value."""
        stmt = select(Keyword).where(Keyword.word == word)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Keyword]:
        """Fetch a paginated list of keywords."""
        stmt = select(Keyword).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create(self, schema: KeywordCreate) -> Keyword:
        """Create a new keyword record."""
        # Переводим слово в нижний регистр для унификации поиска
        db_obj = Keyword(word=schema.word.lower())
        self.session.add(db_obj)

        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def update(self, db_obj: Keyword, schema: KeywordUpdate) -> Keyword:
        """Update an existing keyword record."""
        update_data = schema.model_dump(exclude_unset=True)

        if "word" in update_data and update_data["word"]:
            # Принудительный нижний регистр при обновлении
            db_obj.word = update_data["word"].lower()

        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def delete(self, db_obj: Keyword) -> None:
        """Delete a keyword record."""
        await self.session.delete(db_obj)
        await self.session.commit()