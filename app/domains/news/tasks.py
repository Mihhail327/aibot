import asyncio
import logging
from datetime import datetime, UTC
from typing import Any, cast
from celery import shared_task

from app.core.config import settings
from app.core.database import async_session_maker
from app.domains.keywords.repository import KeywordRepository
from app.domains.news.repository import NewsItemRepository
from app.domains.news.schemas import NewsItemCreate
from app.domains.sources.repository import SourceRepository
from app.infrastructure.parsers.telegram import TelegramChannelParser
from app.infrastructure.parsers.rss_parser import RSSParser
from app.infrastructure.telegram.client import TelegramParserClient
from app.domains.posts.tasks import process_and_publish_post

logger = logging.getLogger(__name__)


async def _run_parsing_pipeline() -> None:
    """Internal asynchronous pipeline for parsing and saving news from active sources."""
    async with async_session_maker() as session:
        source_repo = SourceRepository(session)
        keyword_repo = KeywordRepository(session)
        news_repo = NewsItemRepository(session)

        active_sources = await source_repo.get_all(is_active=True)
        if not active_sources:
            logger.info("Нет активных источников для парсинга.")
            return

        keywords_db = await keyword_repo.get_all()
        keywords_list = [k.word for k in keywords_db]

        client = TelegramParserClient(
            api_id=settings.TELEGRAM_API_ID,
            api_hash=settings.TELEGRAM_API_HASH.get_secret_value(),
            session_string=settings.TELEGRAM_SESSION_STRING.get_secret_value(),
        )

        async with client:
            telegram_parser = TelegramChannelParser(client)
            rss_parser = RSSParser()

            for source in active_sources:
                logger.info(f"Парсинг источника: {source.url}")
                
                # Определяем тип парсинга по структуре URL или наличию rss в адресе
                if "t.me" in source.url or "telegram" in source.url:
                    raw_messages = await telegram_parser.fetch_recent_messages(source.url, limit=20)
                    filtered_messages = telegram_parser.filter_by_keywords(raw_messages, keywords_list)
                    
                    saved_count = 0
                    for msg in filtered_messages:
                        if not msg.text:
                            continue
                            
                        msg_url = f"{source.url}/{msg.id}"
                        existing_news = await news_repo.get_by_url(msg_url)
                        
                        if not existing_news:
                            media_path = await telegram_parser.download_media_for_message(msg)
                            title_text = msg.text[:50] + "..." if len(msg.text) > 50 else msg.text
                            news_schema = NewsItemCreate(
                                title=title_text,
                                url=msg_url,
                                summary=msg.text,
                                source=source.url,
                                published_at=msg.date or datetime.now(UTC),
                                raw_text=msg.text,
                                media_path=media_path
                            )
                            news_item = await news_repo.create(news_schema)
                            saved_count += 1
                            
                            cast(Any, process_and_publish_post).delay(
                                news_id=str(news_item.id),
                                title=news_item.title,
                                text=news_item.raw_text,
                                media_path=news_item.media_path
                            )

                            
                    logger.info(f"Telegram источник {source.url}: сохранено {saved_count} новых записей.")
                else:
                    rss_items = await rss_parser.fetch_feed(source.url, limit=20)
                    
                    saved_count = 0
                    for item in rss_items:
                        existing_news = await news_repo.get_by_url(item.url)
                        
                        if not existing_news:
                            news_schema = NewsItemCreate(
                                title=item.title,
                                url=item.url,
                                summary=item.summary,
                                source=source.url,
                                published_at=item.published_at,
                                raw_text=item.summary
                            )
                            news_item = await news_repo.create(news_schema)
                            saved_count += 1
                            
                            cast(Any, process_and_publish_post).delay(
                                news_id=str(news_item.id),
                                title=news_item.title,
                                text=news_item.raw_text
                            )
                            
                    logger.info(f"RSS источник {source.url}: сохранено {saved_count} новых записей.")


@shared_task(name="news.parse_channels")  # type: ignore[misc, untyped-decorator, unused-ignore]
def parse_channels_task() -> str:
    """
    Celery task to trigger the parsing pipeline.
    Uses @shared_task to decouple from the specific Celery app instance.
    """
    logger.info("Запуск задачи сбора новостей...")
    asyncio.run(_run_parsing_pipeline())
    return "Сбор новостей успешно завершен."