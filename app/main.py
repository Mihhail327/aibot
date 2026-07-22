from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import BaseAPIException
from app.domains.sources.router import router as sources_router
from app.domains.news.router import router as news_router
from app.domains.keywords.router import router as keywords_router

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
    # Убираем trailing slash для консистентности origins
    allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
# Все API эндпоинты будут доступны по префиксу /api/v1 (например, /api/v1/news/)
app.include_router(sources_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(keywords_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}