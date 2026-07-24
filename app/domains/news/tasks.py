import asyncio
import logging
from datetime import datetime, UTC

from celery import shared_task

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.domains.keywords.repository import KeywordRepository
from app.domains.news.repository import NewsItemRepository
from app.domains.news.schemas import NewsItemCreate
from app.domains.sources.repository import SourceRepository
from app.infrastructure.parsers.telegram import TelegramChannelParser
from app.infrastructure.telegram.client import TelegramParserClient

logger = logging.getLogger(__name__)


async def _run_parsing_pipeline() -> None:
    """Internal asynchronous pipeline for parsing and saving news."""
    async with AsyncSessionLocal() as session:
        source_repo = SourceRepository(session)
        keyword_repo = KeywordRepository(session)
        news_repo = NewsItemRepository(session)

        active_sources = await source_repo.get_all(is_active=True)
        if not active_sources:
            logger.info("Нет активных источников для парсинга.")
            return

        keywords_db = await keyword_repo.get_all()
        keywords = [k.word for k in keywords_db]

        client = TelegramParserClient(
            api_id=settings.TELEGRAM_API_ID,
            api_hash=settings.TELEGRAM_API_HASH.get_secret_value(),
            session_string=settings.TELEGRAM_SESSION_STRING.get_secret_value(),
        )

        async with client:
            parser = TelegramChannelParser(client)
            
            for source in active_sources:
                logger.info(f"Парсинг источника: {source.url}")
                raw_messages = await parser.fetch_recent_messages(source.url, limit=20)
                filtered_messages = parser.filter_by_keywords(raw_messages, keywords)
                
                saved_count = 0
                for msg in filtered_messages:
                    if not msg.text:
                        continue
                        
                    msg_url = f"{source.url}/{msg.id}"
                    existing_news = await news_repo.get_by_url(msg_url)
                    
                    if not existing_news:
                        title_text = msg.text[:50] + "..." if len(msg.text) > 50 else msg.text
                        news_schema = NewsItemCreate(
                            title=title_text,
                            url=msg_url,
                            summary=msg.text,
                            source=source.url,
                            published_at=msg.date or datetime.now(UTC),
                            raw_text=msg.text
                        )
                        await news_repo.create(news_schema)
                        saved_count += 1
                        
                logger.info(f"Источник {source.url}: сохранено {saved_count} новых записей.")


# Точечное подавление ошибки нетипизированного декоратора
@shared_task(name="news.parse_channels")  # type: ignore[untyped-decorator]
def parse_channels_task() -> str:
    """
    Celery task to trigger the parsing pipeline.
    Uses @shared_task to decouple from the specific Celery app instance.
    """
    logger.info("Запуск задачи сбора новостей...")
    asyncio.run(_run_parsing_pipeline())
    return "Сбор новостей успешно завершен."