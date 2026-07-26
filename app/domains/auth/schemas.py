from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Standard OAuth2 token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordSetup(BaseModel):
    """Schema for setting or resetting the master password."""
    new_password: str = Field(..., min_length=1, description="Новый мастер-пароль")


InviteSetup = PasswordSetup


class RefreshRequest(BaseModel):
    """Schema for refreshing access token."""
    refresh_token: str = Field(...)