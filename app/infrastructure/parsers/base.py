from abc import ABC, abstractmethod
from typing import Sequence

from app.domains.news.schemas import NewsItemCreate

class BaseParser(ABC):
    """
    Abstract base class for all news parsers.
    Enforces a strict contract for data extraction.
    """

    @abstractmethod
    async def fetch_news(self, source_url: str, limit: int = 20) -> list[NewsItemCreate]:
        """Fetch data from source and return standardized NewsItemCreate schemas."""
        pass

    @abstractmethod
    def filter_by_keywords(self, items: list[NewsItemCreate], keywords: Sequence[str]) -> list[NewsItemCreate]:
        """Filter parsed items against active keywords."""
        pass