# mypy: disable-error-code="prop-decorator"
from pydantic import computed_field, SecretStr, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_core import MultiHostUrl

class Settings(BaseSettings):
    """
    Application settings, loaded and validated from environment variables.
    Provides a single source of truth for all configurations.
    """
    # Project info
    PROJECT_NAME: str = "AI Telegram Publisher"
    VERSION: str = "1.0.0"

    # Security
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    # Database Settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Constructs the asyncpg database URI from individual components."""
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ).unicode_string()
    
    # Redis & Celery Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB_CACHE: int = 0
    REDIS_DB_CELERY: int = 1

    @computed_field 
    @property
    def REDIS_CACHE_URL(self) -> str: 
        """Constructs the Redis connection URL for the cache service."""
        # Формируем URL для дедупликации новостей
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_CACHE}"
    
    @computed_field
    @property
    def REDIS_CELERY_URL(self) -> str:
        """Constructs the Redis connection URL for the Celery broker."""
        # Формируем URL для очереди задач Celery
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_CELERY}"
    
    # External APIs Integrations
    # SecretStr предотвращает случайный вывод токенов в логи (будет напечатано '**********')
    OPENAI_API_KEY: SecretStr

    # Telegram Bot API (aiogram - for publishing)
    TELEGRAM_BOT_TOKEN: SecretStr

    # Telegram MTProto API (Telethon - for parsing)
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: SecretStr

    # Настройки загрузки
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Игнорируем переменные из .env, которые не описаны в классе
    )

# Экземпляр настроек импортируется в других модулях (Singleton Pattern)
settings =  Settings() # type: ignore[call-arg]