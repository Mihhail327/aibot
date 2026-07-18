from datetime import datetime, UTC

from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin

@declarative_mixin
class TimestampMixin:
    """Base mixin to automatically add creation and update timestamps to any SQLAlchemy model."""
    
    # Используем timezone-aware UTC время 
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )