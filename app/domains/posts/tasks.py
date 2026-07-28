import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID
from celery import Task, shared_task
from sqlalchemy import select

from app.core.database import async_session_maker
from app.domains.posts.models import Post, PostStatus
from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.telegram.publisher import TelegramPublisher

logger = logging.getLogger(__name__)


async def _async_process_and_publish(
    self: Task, 
    news_id: str, 
    title: str, 
    text: str, 
    media_path: str | None = None
) -> bool:
    """
    Asynchronous core logic for the Celery task enforcing FSM states 
    and preventing duplicate publications.
    """
    logger.info(f"Starting processing for news_id: {news_id}, title: '{title}', media: '{media_path}'")
    news_uuid = UUID(news_id)

    async with async_session_maker() as session:
        # 1. Проверяем, не был ли пост уже успешно опубликован или взят в обработку (Защита от дублей)
        result = await session.execute(select(Post).where(Post.news_id == news_uuid))
        existing_post = result.scalar_one_or_none()

        if existing_post and existing_post.status == PostStatus.PUBLISHED:
            logger.info(f"Пост для новости {news_id} уже опубликован. Пропуск.")
            return True

        if existing_post and existing_post.status == PostStatus.PROCESSING:
            logger.info(f"Пост для новости {news_id} уже находится в обработке. Пропуск.")
            return True

        ai_generator = OpenAIGenerator()
        publisher = TelegramPublisher()

        # 2. Сохранение или обновление статуса в PROCESSING
        if not existing_post:
            post = Post(
                news_id=news_uuid,
                generated_text="",
                status=PostStatus.PROCESSING
            )
            session.add(post)
            await session.commit()
            await session.refresh(post)
        else:
            post = existing_post
            post.status = PostStatus.PROCESSING
            await session.commit()

        # 3. Генерация текста через OpenAI
        try:
            generated_content = await ai_generator.generate_post(title=title, text=text)
            post.generated_text = generated_content
            post.status = PostStatus.GENERATED
            await session.commit()
        except Exception as exc:
            logger.error(f"Ошибка генерации AI для новости {news_id}: {exc}")
            post.status = PostStatus.FAILED
            await session.commit()
            if hasattr(self, "retry"):
                raise self.retry(exc=exc)
            raise

        # 4. Публикация в Telegram (с картинкой или без)
        try:
            success = await publisher.send_post(text=generated_content, media_path=media_path)
            if success:
                post.status = PostStatus.PUBLISHED
                post.published_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info(f"Пост {post.id} (news_id: {news_id}) успешно опубликован.")
                return True
            else:
                raise RuntimeError("Telegram publisher returned False status.")
        except Exception as exc:
            logger.error(f"Ошибка публикации поста в Telegram для новости {news_id}: {exc}")
            post.status = PostStatus.FAILED
            await session.commit()
            if hasattr(self, "retry"):
                raise self.retry(exc=exc)
            raise


@shared_task(  # type: ignore[misc, untyped-decorator, unused-ignore]
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    name="posts.process_and_publish"
)
def process_and_publish_post(
    self: Task, 
    news_id: str, 
    title: str, 
    text: str, 
    media_path: str | None = None
) -> bool:
    """
    Synchronous Celery task wrapper with FSM and duplicate guard.
    """
    return asyncio.run(_async_process_and_publish(self, news_id, title, text, media_path))