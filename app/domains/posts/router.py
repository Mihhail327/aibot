import uuid
from typing import Sequence
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.posts.models import Post
from app.domains.posts.repository import PostRepository
from app.domains.posts.schemas import PostCreate, PostResponse, PostUpdate
from app.domains.posts.service import PostService

# Инфраструктурные импорты (убедись, что пути соответствуют твоей архитектуре)
from app.domains.news.repository import NewsItemRepository
from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.telegram.publisher import TelegramPublisher

# Изолированный роутер для сгенерированных постов
router = APIRouter(prefix="/posts", tags=["Posts"])


def get_post_service(session: AsyncSession = Depends(get_db)) -> PostService:
    """
    Dependency Injection factory for PostService.
    Assembles the complete object graph (repositories and external adapters).
    """
    # Инициализация слоя данных (Data Layer)
    post_repository = PostRepository(session)
    news_repository = NewsItemRepository(session)
    
    # Инициализация слоя адаптеров (Infrastructure Layer)
    ai_generator = OpenAIGenerator()
    telegram_publisher = TelegramPublisher()

    # Сборка и возврат сервиса-оркестратора
    return PostService(
        repository=post_repository,
        news_repository=news_repository,
        ai_generator=ai_generator,
        telegram_publisher=telegram_publisher
    )


class GenerateTestRequest(BaseModel):
    """Request schema for manual AI generation testing."""
    title: str = Field(..., description="News title for generation")
    text: str = Field(..., description="News text or description")


class GenerateTestResponse(BaseModel):
    """Response schema containing the generated AI post."""
    generated_text: str = Field(..., description="Generated AI post content")


@router.post("/generate", response_model=GenerateTestResponse, status_code=status.HTTP_200_OK)
async def test_ai_generation(payload: GenerateTestRequest) -> GenerateTestResponse:
    """
    Manual testing endpoint for AI post generation via OpenAI GPT-4 using title and text.
    """
    ai_generator = OpenAIGenerator()
    generated_content = await ai_generator.generate_post(title=payload.title, text=payload.text)
    return GenerateTestResponse(generated_text=generated_content)


@router.post("/generate/{news_id}", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def generate_post_from_news(
    news_id: uuid.UUID,
    service: PostService = Depends(get_post_service),
) -> Post:
    """
    Generate an AI post for a specific news item and save it to the database.
    Status will be set to GENERATED.
    """
    # Вся логика работы с OpenAI скрыта в сервисном слое
    return await service.generate_and_save_post(news_id)


@router.post("/{post_id}/publish", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def publish_post_to_telegram(
    post_id: int,
    service: PostService = Depends(get_post_service),
) -> Post:
    """
    Publish a previously generated post to Telegram and update its status to PUBLISHED.
    """
    # Делегируем отправку сообщения и обновление статуса в БД
    return await service.publish_post(post_id)


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    schema: PostCreate,
    service: PostService = Depends(get_post_service),
) -> Post:
    """Create a new AI-generated post manually (bypass AI generation)."""
    return await service.create_post(schema)


@router.get("/", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def get_posts_list(
    skip: int = 0,
    limit: int = 100,
    service: PostService = Depends(get_post_service),
) -> Sequence[Post]:
    """Retrieve a paginated list of posts."""
    return await service.get_all_posts(skip=skip, limit=limit)


@router.get("/news/{news_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post_by_news_id(
    news_id: uuid.UUID,
    service: PostService = Depends(get_post_service),
) -> Post:
    """Retrieve a post linked to a specific news item UUID."""
    return await service.get_post_by_news(news_id)


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post_by_id(
    post_id: int,
    service: PostService = Depends(get_post_service),
) -> Post:
    """Retrieve a specific post by its ID."""
    return await service.get_post(post_id)


@router.patch("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def update_post(
    post_id: int,
    schema: PostUpdate,
    service: PostService = Depends(get_post_service),
) -> Post:
    """Partially update a post (e.g., manual text correction before publishing)."""
    return await service.update_post(post_id, schema)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    service: PostService = Depends(get_post_service),
) -> None:
    """Delete a post."""
    await service.delete_post(post_id)