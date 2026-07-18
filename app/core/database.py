from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 1. Создаем асинхронный движок (Engine) с пулом соединений
engine = create_async_engine(
    url=settings.SQLALCHEMY_DATABASE_URI,
    echo=False, # В продакшене False. True выводит все SQL-запросы в консоль
    pool_size=20, # Максимальное количество постоянных соединений в пуле
    max_overflow=10, # Сколько дополнительных соединений можно создать при пиковой нагрузке
    pool_pre_ping=True, # Проверка "живости" соединения перед его выдачей из пула (защита от разрывов)
)

# 2. Фабрика сессий (Session Factory)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Критично для асинхронной алхимии (запрещает неявные запросы к БД после коммита)
    autoflush=False,
)

# 3. Базовый класс для всех моделей данных
class Base(DeclarativeBase):
    pass

# 4. Dependency Injection для FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for database sessions.
    Yields a session for the request and ensures it is closed gracefully.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Гарантированное возвращение соединения в пул даже при HTTP 500
            await session.close()