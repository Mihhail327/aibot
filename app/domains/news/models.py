import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import TimestampMixin


class NewsItem(Base, TimestampMixin):
    """SQLAlchemy model representing a parsed raw news item."""
    
    __tablename__ = "news_items"

    # UUID позволяет генерировать детерминированные ID при парсинге
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # URL может отсутствовать (например, если это просто текстовый пост из Telegram)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Храним имя источника или его системный идентификатор
    source: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Timezone-aware datetime для точного планирования
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Хранение исходного текста, специфично для интеграции с Telegram API
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)