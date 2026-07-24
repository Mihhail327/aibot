from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Standard OAuth2 token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class InviteSetup(BaseModel):
    """Schema for setting up the master password via invite link."""
    # Поле должно называться строго invite_token
    invite_token: str = Field(..., description="Секретный JWT токен из инвайт-ссылки")
    new_password: str = Field(..., min_length=8, description="Новый мастер-пароль")


class RefreshRequest(BaseModel):
    """Schema for refreshing access token."""
    refresh_token: str = Field(...)