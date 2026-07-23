import uuid 
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.posts.models import Post, PostStatus
from app.domains.posts.schemas import PostCreate, PostUpdate


class PostRepository:
    """Data Access Layer for the Post domain."""

    def __init__(self, session: AsyncSession) -> None:
        # Инжектим активную сессию БД
        self.session = session

    async def get_by_id(self, post_id: int) -> Post | None:
        """Fetch a post by its primary key."""
        return await self.session.get(Post, post_id)

    async def get_by_news_id(self, news_id: uuid.UUID) -> Post | None:
        """Fetch a post linked to a specific news item."""
        # Используетс для предотвращения повторной генерации поста на одну новость
        stmt = select(Post).where(Post.news_id == news_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_status(self, status: PostStatus, limit: int = 50) -> Sequence[Post]:
        """Fetch post filtered by their publication status."""
        # Критично для Celery воркеров (выборка пула задач на публикацию)
        stmt = select(Post).where(Post.status == status).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Post]:
        """Fetch a paginated list of posts, sorted by newest first."""
        stmt = select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, shema: PostCreate) -> Post:
        """Create a new AI-generated post record."""
        db_obj = Post(**shema.model_dump(exclude_unset=True))
        self.session.add(db_obj)

        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: Post, schema: PostUpdate) -> Post:
        """Update an existing post record (e.g., change stetus, set published_at)."""
        update_data = schema.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Post) -> None:
        """Delete a post record."""
        await self.session.delete(db_obj)
        await self.session.commit()