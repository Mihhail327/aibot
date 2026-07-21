import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID  # noqa: F401
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import TimestampMixin


class PostStatus(str, Enum):
    """Enumeration for AI post publication states."""
    
    NEW = "new"
    GENERATED = "generated"
    PUBLISHED = "published"
    FAILED = "failed"


class Post(Base, TimestampMixin):
    """SQLAlchemy model representing an AI-generated post for Telegram."""
    
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Жесткая привязка к сырой новости с каскадным удалением
    news_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("news_items.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Текст, который вернул OpenAI
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Фактическое время публикации (может быть пустым, пока статус != PUBLISHED)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Машинное состояние (FSM) для контроля публикаций
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus), 
        default=PostStatus.NEW, 
        nullable=False, 
        index=True
    )