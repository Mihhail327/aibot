import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- ИНТЕГРАЦИЯ С ЯДРОМ ПРИЛОЖЕНИЯ ---
import os
import sys
# Добавляем корень проекта в sys.path, чтобы корректно работали импорты app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.database import Base
# ВАЖНО: Импортируем модель, чтобы Alembic увидел ее в Base.metadata
from app.domains.sources.models import Source # noqa: F401

from app.domains.keywords.models import Keyword # noqa: F401
from app.domains.news.models import NewsItem # noqa: F401
from app.domains.posts.models import Post # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Передаем метаданные нашей ORM для поддержки autogenerate
target_metadata = Base.metadata
# -----------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Используем URL из Pydantic settings напрямую
    url = settings.SQLALCHEMY_DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run actual synchronous migrations within the async loop."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine and associate a connection with the context."""
    configuration = config.get_section(config.config_ini_section, {})
    
    # Принудительно заменяем URL из alembic.ini на наш рабочий DSN из настроек
    configuration["sqlalchemy.url"] = settings.SQLALCHEMY_DATABASE_URI

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Фикс для асинхронного драйвера psycopg3 при локальной разработке на Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()