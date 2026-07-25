import uuid
from typing import Sequence

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.posts.models import Post, PostStatus
from app.domains.posts.repository import PostRepository
from app.domains.posts.schemas import PostCreate, PostUpdate


class PostService:
    """
    Business logic layer for the AI-generated Post domain.
    Orchestrates CRUD operations and enforces domain invariants.
    """

    def __init__(self, repository: PostRepository) -> None:
        """
        Initialize the PostService.
        
        Args:
            repository: Injected repository instance for DB isolation.
        """
        # Инжектим абстракцию базы данных для изоляции I/O операций
        self.repository = repository

    async def get_post(self, post_id: int) -> Post:
        """
        Fetch a single post by its internal ID.
        
        Args:
            post_id: The primary key of the post.
            
        Returns:
            Post: The retrieved post model.
            
        Raises:
            NotFoundException: If the post does not exist in the database.
        """
        post = await self.repository.get_by_id(post_id)
        if not post:
            raise NotFoundException(detail=f"Пост с ID {post_id} не найден.")
        return post

    async def get_post_by_news(self, news_id: uuid.UUID) -> Post:
        """
        Fetch a post linked to a specific external news item.
        
        Args:
            news_id: The unique identifier of the source news item.
            
        Returns:
            Post: The retrieved post model.
            
        Raises:
            NotFoundException: If no post is linked to the given news_id.
        """
        post = await self.repository.get_by_news_id(news_id)
        if not post:
            raise NotFoundException(detail=f"Пост для новости {news_id} не найден.")
        return post

    async def get_posts_by_status(self, status: PostStatus, limit: int = 50) -> Sequence[Post]:
        """
        Fetch a batch of posts filtered by their publication status.
        Optimized for processing queues (e.g., Celery workers fetching pending posts).
        
        Args:
            status: The target status to filter by (e.g., DRAFT, PUBLISHED).
            limit: Maximum number of records to return.
            
        Returns:
            Sequence[Post]: A list of matching post models.
        """
        return await self.repository.get_by_status(status=status, limit=limit)

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> Sequence[Post]:
        """
        Fetch a paginated list of all posts.
        
        Args:
            skip: Number of records to offset.
            limit: Maximum number of records to return.
            
        Returns:
            Sequence[Post]: A list of post models.
        """
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create_post(self, schema: PostCreate) -> Post:
        """
        Create a new post record while enforcing domain invariants.
        Ensures strict 1:1 mapping between a news item and a post.
        
        Args:
            schema: Validated creation data payload.
            
        Returns:
            Post: The newly created post model.
            
        Raises:
            DuplicateResourceException: If a post already exists for this news_id.
        """
        existing_post = await self.repository.get_by_news_id(schema.news_id)

        if existing_post:
            # Предотвращаем дубликацию вызовов к OpenAI и защиту от двойной публикации
            raise DuplicateResourceException(
                detail=f"Пост для новости {schema.news_id} уже существует (ID: {existing_post.id})."
            )

        return await self.repository.create(schema)

    async def update_post(self, post_id: int, schema: PostUpdate) -> Post:
        """
        Update an existing post (e.g., status, content, or publication time).
        
        Args:
            post_id: The primary key of the post to update.
            schema: Validated update data payload (partial).
            
        Returns:
            Post: The updated post model.
            
        Raises:
            NotFoundException: If the post does not exist.
        """
        post = await self.get_post(post_id)
        return await self.repository.update(db_obj=post, schema=schema)

    async def delete_post(self, post_id: int) -> None:
        """
        Hard delete a post record from the system.
        
        Args:
            post_id: The primary key of the post to delete.
            
        Raises:
            NotFoundException: If the post does not exist.
        """
        post = await self.get_post(post_id)
        await self.repository.delete(post)