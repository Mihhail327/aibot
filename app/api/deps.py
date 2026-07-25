"""
FastAPI Dependencies for Dependency Injection.
Author: Mihhail327
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.domains.posts.repository import PostRepository
from app.domains.posts.service import PostService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an asynchronous database session per request lifecycle.
    Ensures safe connection pooling and automatic rollback/close.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_post_service(session: AsyncSession = Depends(get_db_session)) -> PostService:
    """
    Assemble and provide the PostService with an injected repository and session.
    """
    repository = PostRepository(session)
    return PostService(repository)