import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_invite_token,  
)
from app.domains.auth.models import AdminSettings
from app.domains.auth.schemas import InviteSetup, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Authenticate via master password and return JWT tokens."""
    # Получаем единственный хэш из БД
    stmt = select(AdminSettings).limit(1)
    result = await session.execute(stmt)
    admin_record = result.scalar_one_or_none()

    if not admin_record:
        # Запрет несанкционированной инициализации при логине
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Мастер-пароль еще не настроен. Используйте /auth/setup с invite_token."
        )
        
    if not verify_password(form_data.password, admin_record.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect master password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерируем пару токенов
    return {
        "access_token": create_access_token(),
        "refresh_token": create_refresh_token(),
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(schema: RefreshRequest) -> dict[str, str]:
    """Issue a new access token using a valid refresh token."""
    try:
        payload = jwt.decode(
            schema.refresh_token, 
            settings.SECRET_KEY.get_secret_value(), 
            algorithms=["HS256"]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token type"
            )
            
        return {
            "access_token": create_access_token(),
            "refresh_token": create_refresh_token(),
            "token_type": "bearer"
        }
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid refresh token"
        )


@router.post("/setup", status_code=status.HTTP_200_OK)
async def setup_master_password(
    schema: InviteSetup, 
    session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Set or reset the master password using a valid invite token."""
    # Строгая валидация токена приглашения
    if not verify_invite_token(schema.invite_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired invite token"
        )

    stmt = select(AdminSettings).limit(1)
    result = await session.execute(stmt)
    admin_record = result.scalar_one_or_none()

    new_hash = get_password_hash(schema.password)

    if admin_record:
        # Обновление существующего пароля
        admin_record.password_hash = new_hash
    else:
        # Инициализация первого пароля
        admin_record = AdminSettings(password_hash=new_hash)
        session.add(admin_record)

    await session.commit()
    return {"message": "Master password successfully set"}