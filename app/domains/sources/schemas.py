from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    """Supported source types for parsing tasks routing."""
    TELEGRAM = "telegram"
    RSS = "rss"
    WEB = "web"


class SourceBase(BaseModel):
    """Base schema with common attributes."""
    
    # Field(...) означает, что поле обязательно. Добавляем метаданные для Swagger.
    name: str = Field(..., max_length=255, description="Человекочитаемое название источника")
    
    # Мы используем str, а не HttpUrl, так как Telegram-источники могут начинаться с '@'
    url: str = Field(..., max_length=500, description="URL или Telegram-хэндл (например, @ai_news или https://...)")
    
    is_active: bool = Field(default=True, description="Флаг активности для планировщика задач")
    source_type: SourceType = Field(default=SourceType.TELEGRAM, description="Тип контента для Celery воркеров")


class SourceCreate(SourceBase):
    """Schema for creating a new source."""
    # Наследует все поля из SourceBase как есть
    pass


class SourceUpdate(BaseModel):
    """Schema for partial updates (PATCH). All fields are optional."""
    
    name: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)
    source_type: Optional[SourceType] = Field(default=None)


class SourceResponse(SourceBase):
    """Schema for API responses. Includes database-generated fields."""
    
    id: int
    created_at: datetime
    updated_at: datetime

    # Конфигурация Pydantic V2 для чтения данных напрямую из объектов SQLAlchemy
    model_config = ConfigDict(from_attributes=True)