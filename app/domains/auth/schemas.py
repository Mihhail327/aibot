from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Standard OAuth2 token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordSetup(BaseModel):
    """
    Schema for master password setup or reset.
    """
    password: str = Field(..., min_length=8, description="Новый мастер-пароль")
    invite_token: str = Field(..., description="Токен приглашения для установки пароля")


InviteSetup = PasswordSetup


class RefreshRequest(BaseModel):
    """Schema for refreshing access token."""
    refresh_token: str = Field(...)