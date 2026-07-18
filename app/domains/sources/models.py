from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import TimestampMixin


class Source(Base, TimestampMixin):
    """SQLAlchemy model representing a data source for parsing (e.g., Telegram channel or RSS feed)."""
    
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Человекочитаемое название (например, "Новости AI")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Уникальный идентификатор ресурса (например, @ai_news_tg или https://...)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    
    # Флаг для временного отключения парсинга источника
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Тип источника для маршрутизации воркеров Celery (telegram, rss, web)
    source_type: Mapped[str] = mapped_column(String(50), default="telegram", nullable=False)