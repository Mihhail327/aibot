from pydantic import BaseModel, ConfigDict, Field


class KeywordBase(BaseModel):
    """Base schema for Keyword with common validated attributes."""

    # Ограничение длины зеркалирует String(100) из БД
    word: str = Field(..., max_length=100, description="Ключевое слово или фраза для фильтрации")


class KeywordCreate(KeywordBase):
    """Schema for creating a new keyword."""
    pass 


class KeywordUpdate(BaseModel):
    """Schema for partial updates (PATCH) of an existing keyword."""

    word: str | None = Field(default=None, max_length=100)


class KeywordResponse(KeywordBase):
    """Schema for API responses, including database-generated metadata."""

    id: int

    model_config = ConfigDict(from_attributes=True)