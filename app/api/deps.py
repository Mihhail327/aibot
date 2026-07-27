from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.domains.posts.repository import PostRepository
from app.domains.posts.service import PostService

# ДОБАВЛЕННЫЕ ИМПОРТЫ
from app.domains.news.repository import NewsItemRepository
from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.telegram.publisher import TelegramPublisher


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
    Assemble and provide the PostService with all injected repositories and adapters.
    Acts as the Composition Root for the Posts domain.
    """
    # Инициализация слоя данных
    post_repository = PostRepository(session)
    news_repository = NewsItemRepository(session)
    
    # Инициализация инфраструктурного слоя
    ai_generator = OpenAIGenerator()
    telegram_publisher = TelegramPublisher()

    # Сборка графа зависимостей
    return PostService(
        repository=post_repository,
        news_repository=news_repository,
        ai_generator=ai_generator,
        telegram_publisher=telegram_publisher
    )