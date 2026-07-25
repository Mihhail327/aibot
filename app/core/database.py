"""
Database configuration and session management (SQLAlchemy 2.0 Async).
Author: Mihhail327
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 1. Создаем асинхронный движок (Engine) с пулом соединений
engine = create_async_engine(
    url=settings.SQLALCHEMY_DATABASE_URI,
    echo=False,  # В продакшене False. True выводит все SQL-запросы в консоль
    pool_size=20,  # Максимальное количество постоянных соединений в пуле
    max_overflow=10,  # Сколько дополнительных соединений можно создать при пиковой нагрузке
    pool_pre_ping=True,  # Проверка "живости" соединения перед его выдачей из пула
)

# 2. Фабрика сессий (Session Factory). 
# Имя async_session_maker используется для единого стандарта во всем проекте.
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Критично для асинхронной алхимии
    autoflush=False,
)

# 3. Базовый класс для всех моделей данных
class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""
    pass

# 4. Dependency Injection для FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for database sessions.
    Yields a session for the request and ensures it is closed gracefully.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Гарантированное возвращение соединения в пул даже при HTTP 500
            await session.close()