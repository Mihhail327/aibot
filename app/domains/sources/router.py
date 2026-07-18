from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.domains.sources.models import Source
from app.domains.sources.repository import SourceRepository
from app.domains.sources.schemas import SourceCreate, SourceResponse, SourceUpdate
from app.domains.sources.service import SourceService

router = APIRouter(prefix="/sources", tags=["Sources"])

def get_source_service(session: AsyncSession = Depends(get_db)) -> SourceService:
    """Dependency Injection factory for SourceService."""
    repository = SourceRepository(session)
    return SourceService(repository)

@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    schema: SourceCreate,
    service: SourceService = Depends(get_source_service),
) -> Source:  
    return await service.create_source(schema)

@router.get("/", response_model=list[SourceResponse], status_code=status.HTTP_200_OK)
async def get_sources(
    skip: int = 0,
    limit: int = 100,
    service: SourceService = Depends(get_source_service),
) -> Sequence[Source]:  
    return await service.get_all_sources(skip=skip, limit=limit)

@router.get("/{source_id}", response_model=SourceResponse, status_code=status.HTTP_200_OK)
async def get_source(
    source_id: int,
    service: SourceService = Depends(get_source_service),
) -> Source:  
    return await service.get_source(source_id)

@router.patch("/{source_id}", response_model=SourceResponse, status_code=status.HTTP_200_OK)
async def update_source(
    source_id: int,
    schema: SourceUpdate,
    service: SourceService = Depends(get_source_service),
) -> Source:  
    return await service.update_source(source_id, schema)

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    service: SourceService = Depends(get_source_service),
) -> None:
    await service.delete_source(source_id)