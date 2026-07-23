import uuid
from typing import Sequence

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.posts.models import Post, PostStatus
from app.domains.posts.repository import PostRepository
from app.domains.posts.schemas import PostCreate, PostUpdate

class PostService:
    """Business logic layer for the AI-generated Post domain."""

    def __init__(self, repository: PostRepository) -> None:
        # Инжектим репозиторий для изоляции доступа к БД
        self.repository = repository

    async def get_post(self, post_id: int) -> Post:
        """Fetch a single post by ID, raising an exception if not found"""
        post = await self.repository.get_by_id(post_id)
        if not post:
            raise NotFoundException(detail=f"Пост с ID {post_id} не найден.")
        return post

    async def get_post_by_news(self, news_id: uuid.UUID) -> Post:
        """Fetch a post linked to a specific news item."""
        post = await self.repository.get_by_news_id(news_id)
        if not post:
            raise NotFoundException(detail=f"Пост для новости {news_id} не найден.")
        return post

    async def get_posts_by_status(self, status: PostStatus, limit: int = 50) -> Sequence[Post]:
        """Fetch a batch of posts filtered by status (used for Celery workers)"""
        return await self.repository.get_by_status(status=status, limit=limit)

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> Sequence[Post]:
        """Fetch a paginated list of all posts."""
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create_post(self, schema: PostCreate) -> Post:
        """Create a new post with validation ensuring one post per news item."""
        existing_post = await self.repository.get_by_news_id(schema.news_id)

        if existing_post:
            # Предотвращаем дубликацию запросов к OpenAI и спам в каналах
            raise DuplicateResourceException(
                detail=f"Пост для новости {schema.news_id} уже существует (ID: {existing_post.id})."
            )

        return await self.repository.create(schema)

    async def update_post(self, post_id: int, schema: PostUpdate) -> Post:
        """Update a post`s satus, content, or publication time."""
        post = await self.get_post(post_id)
        return await self.repository.update(db_obj=post, schema=schema)

    async def delete_post(self, post_id: int) -> None:
        """Delete a post record."""
        post = await self.get_post(post_id)
        await self.repository.delete(post)