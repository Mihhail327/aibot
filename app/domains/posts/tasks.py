import asyncio
import logging
from celery import Task, shared_task

from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.telegram.publisher import TelegramPublisher

logger = logging.getLogger(__name__)


async def _async_process_and_publish(title: str, text: str) -> bool:
    """
    Asynchronous core logic for the Celery task.
    Orchestrates the AI generation and Telegram publishing.
    """
    logger.info(f"Starting processing for post: '{title}'")
    
    ai_generator = OpenAIGenerator()
    publisher = TelegramPublisher()
    
    generated_content = await ai_generator.generate_post(title=title, text=text)
    success = await publisher.send_post(text=generated_content)
    
    return success


@shared_task(  # type: ignore[misc]
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    name="posts.process_and_publish"
)
def process_and_publish_post(self: Task, title: str, text: str) -> bool:
    """
    Synchronous Celery task wrapper.
    Receives raw parser data and triggers the async pipeline.
    
    Args:
        self: The Celery task instance (bound via bind=True).
        title: The original news title.
        text: The original news content.
        
    Returns:
        bool: True if fully processed and published.
    """
    return asyncio.run(_async_process_and_publish(title, text))