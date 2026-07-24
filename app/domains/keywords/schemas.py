from pydantic import BaseModel, Field, field_validator, ConfigDict

class KeywordBase(BaseModel):
    """Base schema for Keyword with common validated attributes."""
    word: str = Field(..., max_length=100, description="Ключевое слово для фильтрации")

    @field_validator("word")
    @classmethod
    def lowercase_word(cls, v: str) -> str:
        """
        Enforce lowercase constraint at the API boundary.
        """
        return v.lower().strip()

class KeywordCreate(KeywordBase):
    """Schema for creating a new keyword."""
    pass 

class KeywordUpdate(BaseModel):
    """Schema for partial updates (PATCH) of an existing keyword."""
    word: str | None = Field(default=None, max_length=100)

    @field_validator("word")
    @classmethod
    def lowercase_word(cls, v: str | None) -> str | None:
        """
        Enforce lowercase constraint for updates.
        Пропускаем None, так как поле опционально.
        """
        return v.lower().strip() if v is not None else v

class KeywordResponse(KeywordBase):
    """Schema for API responses, including database-generated metadata."""
    id: int

    model_config = ConfigDict(from_attributes=True)