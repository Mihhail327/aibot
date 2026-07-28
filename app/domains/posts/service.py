import uuid
from typing import Sequence

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.posts.models import Post, PostStatus
from app.domains.posts.repository import PostRepository
from app.domains.posts.schemas import PostCreate, PostUpdate

# Раскомментируй эти импорты, когда будешь готов интегрировать реальные клиенты
from app.domains.news.repository import NewsItemRepository
from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.telegram.publisher import TelegramPublisher


class PostService:
    """
    Business logic layer for the AI-generated Post domain.
    Orchestrates CRUD operations, AI generation, and Telegram publishing.
    """

    def __init__(
        self, 
        repository: PostRepository,
        news_repository: NewsItemRepository | None = None,
        ai_generator: OpenAIGenerator | None = None,
        telegram_publisher: TelegramPublisher | None = None,
    ) -> None:
        self.repository = repository
        self.news_repository = news_repository
        self.ai_generator = ai_generator or OpenAIGenerator()
        self.telegram_publisher = telegram_publisher or TelegramPublisher()

    # ---------------------------------------------------------
    # CORE CRUD OPERATIONS (Восстановленные методы)
    # ---------------------------------------------------------

    async def get_post(self, post_id: int) -> Post:
        post = await self.repository.get_by_id(post_id)
        if not post:
            raise NotFoundException(detail=f"Пост с ID {post_id} не найден.")
        return post

    async def get_post_by_news(self, news_id: uuid.UUID) -> Post:
        post = await self.repository.get_by_news_id(news_id)
        if not post:
            raise NotFoundException(detail=f"Пост для новости {news_id} не найден.")
        return post

    async def get_posts_by_status(self, status: PostStatus, limit: int = 50) -> Sequence[Post]:
        return await self.repository.get_by_status(status=status, limit=limit)

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> Sequence[Post]:
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create_post(self, schema: PostCreate) -> Post:
        existing_post = await self.repository.get_by_news_id(schema.news_id)
        if existing_post:
            raise DuplicateResourceException(
                detail=f"Пост для новости {schema.news_id} уже существует (ID: {existing_post.id})."
            )
        return await self.repository.create(schema)

    async def update_post(self, post_id: int, schema: PostUpdate) -> Post:
        post = await self.get_post(post_id)
        return await self.repository.update(db_obj=post, schema=schema)

    async def delete_post(self, post_id: int) -> None:
        post = await self.get_post(post_id)
        await self.repository.delete(post)

    # ---------------------------------------------------------
    # COMPLEX BUSINESS FLOWS
    # ---------------------------------------------------------

    async def generate_and_save_post(self, news_id: uuid.UUID) -> Post:
        existing_post = await self.repository.get_by_news_id(news_id)
        if existing_post:
            raise DuplicateResourceException(
                detail=f"Пост для новости {news_id} уже сгенерирован (ID: {existing_post.id})."
            )

        news_item = None
        if self.news_repository:
            news_item = await self.news_repository.get_by_id(news_id)
        
        if not news_item:
            raise NotFoundException(detail=f"Новость с ID {news_id} не найдена.")

        text_content = news_item.raw_text or news_item.summary or ""
        generated_text = await self.ai_generator.generate_post(title=news_item.title, text=text_content)

        schema = PostCreate(
            news_id=news_id,
            generated_text=generated_text,
            status=PostStatus.GENERATED
        )
        return await self.repository.create(schema)

    async def publish_post(self, post_id: int) -> Post:
        post = await self.get_post(post_id)

        if post.status == PostStatus.PUBLISHED:
            raise DuplicateResourceException(
                detail=f"Пост {post_id} уже был опубликован."
            )

        news_media = None
        if self.news_repository and post.news_id:
            news_item = await self.news_repository.get_by_id(post.news_id)
            if news_item:
                news_media = news_item.media_path

        try:
            success = await self.telegram_publisher.send_post(text=post.generated_text, media_path=news_media)
            if not success:
                raise RuntimeError("Telegram publisher returned False status.")
        except Exception:
            update_schema = PostUpdate(status=PostStatus.FAILED)
            await self.update_post(post_id, update_schema)
            raise

        from datetime import datetime, UTC
        update_schema = PostUpdate(status=PostStatus.PUBLISHED, published_at=datetime.now(UTC))
        return await self.update_post(post_id, update_schema)