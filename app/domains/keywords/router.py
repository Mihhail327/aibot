from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.keywords.models import Keyword
from app.domains.keywords.repository import KeywordRepository
from app.domains.keywords.schemas import KeywordCreate, KeywordResponse, KeywordUpdate
from app.domains.keywords.service import KeywordService

# Изолированный роутер для ключевых слов
router = APIRouter(prefix="/keywords", tags=["Keywords"])


def get_keyword_service(session: AsyncSession = Depends(get_db)) -> KeywordService:
    """
    Dependency Injection factory for KeywordService.
    Provides an isolated service instance with the current HTTP request's DB session.
    """
    repository = KeywordRepository(session)
    return KeywordService(repository)


@router.post("/", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    schema: KeywordCreate,
    service: KeywordService = Depends(get_keyword_service),
) -> Keyword:
    """Create a new keyword for news filtering."""
    # Валидация Pydantic уже пройдена, передаем схему в сервис
    return await service.create_keyword(schema)


@router.get("/", response_model=list[KeywordResponse], status_code=status.HTTP_200_OK)
async def get_keywords_list(
    skip: int = 0,
    limit: int = 100,
    service: KeywordService = Depends(get_keyword_service),
) -> Sequence[Keyword]:
    """Retrieve a paginated list of keywords."""
    return await service.get_all_keywords(skip=skip, limit=limit)


@router.get("/{keyword_id}", response_model=KeywordResponse, status_code=status.HTTP_200_OK)
async def get_keyword_by_id(
    keyword_id: int,
    service: KeywordService = Depends(get_keyword_service),
) -> Keyword:
    """Retrieve a specific keyword by its ID."""
    return await service.get_keyword(keyword_id)


@router.patch("/{keyword_id}", response_model=KeywordResponse, status_code=status.HTTP_200_OK)
async def update_keyword(
    keyword_id: int,
    schema: KeywordUpdate,
    service: KeywordService = Depends(get_keyword_service),
) -> Keyword:
    """Partially update a keyword."""
    return await service.update_keyword(keyword_id, schema)


@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: int,
    service: KeywordService = Depends(get_keyword_service),
) -> None:
    """Delete a keyword."""
    # 204 No Content означает успешное выполнение без возврата тела ответа
    await service.delete_keyword(keyword_id)