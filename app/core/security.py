import logging
from datetime import datetime, timedelta, UTC
import jwt
import bcrypt

# Fix passlib 1.7.4 compatibility with bcrypt >= 4.1.0 (trapped AttributeError: module 'bcrypt' has no attribute '__about__')
if not hasattr(bcrypt, "__about__"):
    class _BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "4.0.1")
    bcrypt.__about__ = _BcryptAbout()  # type: ignore[assignment]


from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# Настройка контекста для хэширования паролей (BCrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored hash."""
    # Явное приведение типов (Type Casting) для удовлетворения строгого mypy
    result = pwd_context.verify(plain_password, hashed_password)
    return bool(result)


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for the provided password."""
    # Явное приведение к строке, чтобы отсечь Any от passlib
    result = pwd_context.hash(password)
    return str(result)


def create_access_token(subject: str = "admin") -> str:
    """
    Create a short-lived JWT access token.
    """
    expire = datetime.now(UTC) + timedelta(minutes=30)
    to_encode = {"exp": expire, "sub": subject, "type": "access"}
    
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm="HS256"
    )


def create_refresh_token(subject: str = "admin") -> str:
    """
    Create a long-lived JWT refresh token.
    """
    expire = datetime.now(UTC) + timedelta(days=30)
    to_encode = {"exp": expire, "sub": subject, "type": "refresh"}
    
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(), 
        algorithm="HS256"
    )


def verify_invite_token(token: str) -> bool:
    """
    Verify the validity of a registration invite link.
    """
    if settings.INVITE_TOKEN and token == settings.INVITE_TOKEN.get_secret_value():
        return True

    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY.get_secret_value(), 
            algorithms=["HS256"]
        )
        return payload.get("type") == "invite"
    except jwt.InvalidTokenError:
        return False