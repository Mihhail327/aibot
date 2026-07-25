import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramPublisher:
    """Service for publishing AI-generated content to Telegram channels."""

    def __init__(self) -> None:
        """Initialize the Aiogram Bot instance."""
        # Используем DefaultBotProperties для глобальной установки HTML-разметки
        self.bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

    async def send_post(self, text: str, channel_id: int | str | None = None) -> bool:
        """
        Publish a formatted text post to the target Telegram channel.

        Args:
            text: The AI-generated content.
            channel_id: Optional target channel override.

        Returns:
            bool: True if publication was successful.
            
        Raises:
            Exception: Bubbles up network or API errors to trigger Celery retries.
        """
        target = channel_id or settings.TARGET_CHANNEL_ID

        try:
            # Отправка сообщения в целевой канал
            await self.bot.send_message(chat_id=target, text=text)
            logger.info(f"Post successfully published to {target}")
            return True

        except Exception as exc:
            # Логируем ошибку, но ОБЯЗАТЕЛЬНО пробрасываем дальше (Fail Fast).
            # Это критически важно, чтобы Celery мог сделать retry задачи.
            logger.error(f"Failed to publish to {target}. Error: {exc}")
            raise

        finally:
            # Обязательное закрытие сессии aiohttp во избежание утечек ресурсов
            await self.bot.session.close()