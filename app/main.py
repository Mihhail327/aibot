from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import BaseAPIException
from app.domains.sources.router import router as sources_router

# 1. Инициализация приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# 2. CORS Middleware (Security)
app.add_middleware(
    CORSMiddleware,
    # Убираем trailing slash, который Pydantic V2 автоматически добавляет к AnyHttpUrl
    allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    # Явно указываем разрешенные методы (никаких "*")
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    # Явно указываем разрешенные заголовки для CORS (включая будущий Authorization)
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)

# 3. Глобальный обработчик бизнес-исключений (Contract-First)
@app.exception_handler(BaseAPIException)
async def custom_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Catches all custom business logic exceptions and formats them as standard JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# 4. Регистрация доменных роутеров (Modular Design)
# Добавляем префикс версии API для совместимости в будущем
app.include_router(sources_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}