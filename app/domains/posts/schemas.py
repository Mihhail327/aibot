import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.posts.models import PostStatus


class PostBase(BaseModel):
    """Base schema for Post with common attributes."""

    news_id: uuid.UUID = Field(..., description="ID оригинальной новости (связь)")
    generated_text: str = Field(..., description="Текст поста сгенерированный ИИ")
    status: PostStatus = Field(default=PostStatus.NEW, description="Текущий статус публикации")


class PostCreate(PostBase):
    """Schema for creating a new AI post in the database."""
    pass 


class PostUpdate(BaseModel):
    """Schema for partial updates (PATCH) of an existing post."""
    generated_text: str | None = Field(default=None, description="Скоректированный текст поста")
    published_at: datetime | None = Field(default=None, description="Время фактической публикации")
    status: PostStatus | None = Field(default=None, description="Новый статус публикации")


class PostResponse(PostBase):
    """Schema for API responses, including database-generated metadata."""

    id: int 
    published_at: datetime | None = Field(default=None)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)