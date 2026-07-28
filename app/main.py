from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import BaseAPIException
from app.core.limiter import limiter
from app.core.dependencies import get_current_admin
from app.domains.sources.router import router as sources_router
from app.domains.news.router import router as news_router
from app.domains.keywords.router import router as keywords_router
from app.domains.posts.router import router as posts_router
from app.domains.auth.router import router as auth_router
from app.domains.logs.router import router as logs_router

# 1. Инициализация приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

@app.get("/docs", include_in_schema=False)
async def swagger_redirect() -> RedirectResponse:
    """Redirect to the main API docs."""
    return RedirectResponse(url="/api/docs")

# 2. CORS Middleware (Security)
app.add_middleware(
    CORSMiddleware,
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
# Все API эндпоинты будут доступны по префиксу /api/v1
app.include_router(auth_router, prefix="/api/v1")

protected = [Depends(get_current_admin)]

app.include_router(sources_router, prefix="/api/v1", dependencies=protected)
app.include_router(news_router, prefix="/api/v1", dependencies=protected)
app.include_router(keywords_router, prefix="/api/v1", dependencies=protected)
app.include_router(posts_router, prefix="/api/v1", dependencies=protected)
app.include_router(logs_router, prefix="/api/v1", dependencies=protected)

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}