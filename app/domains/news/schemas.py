import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class NewsItemBase(BaseModel):
    """Base schema for NewsItem with common validated attributes."""
    
    title: str = Field(..., max_length=500, description="Заголовок новости")
    
    # Используем str | None и явно указываем default=None
    url: str | None = Field(default=None, max_length=1000, description="Оригинальная ссылка")
    
    summary: str = Field(..., description="Краткая выжимка или полный текст новости")
    source: str = Field(..., max_length=255, description="Системное имя источника (например, URL канала)")
    published_at: datetime = Field(..., description="Время публикации оригинальной новости")
    
    # Исправленное поле для строгого тайп-чекинга
    raw_text: str | None = Field(default=None, description="Сырой текст для специфичной обработки ИИ")

class NewsItemCreate(NewsItemBase):
    """Schema for creating a new news item. Used primarily by Celery parsing workers."""
    
    id: uuid.UUID | None = Field(
        default=None, 
        description="Предустановленный UUID на основе хэша (для дедупликации)"
    )

class NewsItemUpdate(BaseModel):
    """Schema for partial updates (PATCH) of an existing news item."""
    
    title: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=1000)
    summary: str | None = Field(default=None)
    raw_text: str | None = Field(default=None)

class NewsItemResponse(NewsItemBase):
    """Schema for API responses, including database-generated metadata."""
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)