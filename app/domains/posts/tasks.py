import asyncio
import logging
from celery import shared_task

from app.infrastructure.ai.openai_client import OpenAIGenerator
from app.infrastructure.telegram.publisher import TelegramPublisher

logger = logging.getLogger(__name__)

async def _async_process_and_publisher(title: str, text: str) -> bool:
    """
    Asynchronous core logic for the Celery task.
    Orchestrates the AI generation and Telegram publishing.
    """

    logger.info(f"Starting processing for post: '{title}'")

    # 1. Инициализация адаптеров (в идеале внедряется через DI контейнер, 
    # но для простоты инстанцируем напрямую - YAGNI)
    ai_generator = OpenAIGenerator()
    publisher = TelegramPublisher()

    # 2. Генерация текста через LLM
    logger.debug("Calling AI Generator... ")
    generated_content = await ai_generator.generate_post(title=title, text=text)

    # 3. Публикация готового поста в целевой канал
    logger.debug("Publishing to Telegram... ")
    success = await publisher.send_post(text=generated_content)

    return success

# Отключаем проверку mypy для декоратора Celery, 
# так как он динамически меняет сигнатуру функции
# mypy: disable-error-code="misc"

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception),
    retry_backoff=True,
    retry_backoff_max=600, # Максимальная задержка между попытками - 10 минут
    name="posts.process_and_publish"
)
def process_and_publish_post(self, title: str, text: str) -> bool:
    """
    Synchronous Celery task wrapper.
    Receives raw parser data and triggers the async pipeline.

    Args:
        title: The original news title.
        text: The original news content.

    Returns:
        bool: True if fully processed and published.
    """
    # Запускаем изолированный event loop для выполнения асинхронной логики
    return asyncio.run(_async_process_and_publisher(title, text))