import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# Связываем с эндпоинтом логина для работы Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to protect API endpoints. Validates the JWT access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодируем и валидируем подпись/срок годности токена
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY.get_secret_value(), 
            algorithms=["HS256"]
        )
        
        # Проверяем, что это именно access token
        if payload.get("type") != "access":
            raise credentials_exception
            
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
            
        return sub
        
    except jwt.InvalidTokenError:
        # Перехватываем любые ошибки JWT (ExpiredSignatureError, DecodeError)
        raise credentials_exception