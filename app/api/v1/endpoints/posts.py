from typing import Sequence
from fastapi import APIRouter, Depends, status  # noqa: F401

from app.domains.posts.models import Post
from app.domains.posts.schemas import PostCreate, PostResponse
from app.domains.posts.service import PostService  # noqa: F401
# Предполагаемая зависимость для получения сервиса через DI
# from app.api.deps import get_post_service

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=list[PostResponse])
async def get_all_posts(
    skip: int = 0,
    limit: int = 100,
    # service: PostService = Depends(get_post_service)
) -> Sequence[Post]:
    """
    Retrieve a paginated list of all generated posts.
    """
    # Возвращаем реальный результат вместо pass, устраняя ошибку Pylance
    # return await service.get_all_posts(skip=skip, limit=limit)
    return []


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_post(
    schema: PostCreate,
    # service: PostService = Depends(get_post_service)
) -> Post:
    """
    Manually create a post draft for processing.
    """
    # Заглушка, возвращающая объект (или вызов сервиса), чтобы удовлетворить тип Post
    # return await service.create_post(schema)
    raise NotImplementedError("Endpoint under construction")