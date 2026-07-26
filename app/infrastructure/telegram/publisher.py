import os
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

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

    async def send_post(
        self, 
        text: str, 
        channel_id: int | str | None = None, 
        media_path: str | None = None
    ) -> bool:
        """
        Publish a formatted text post (with optional image) to the target Telegram channel.

        Args:
            text: The AI-generated content.
            channel_id: Optional target channel override.
            media_path: Optional local path to an image file.

        Returns:
            bool: True if publication was successful.
            
        Raises:
            Exception: Bubbles up network or API errors to trigger Celery retries.
        """
        target = channel_id or settings.TARGET_CHANNEL_ID

        try:
            has_media = bool(media_path and os.path.exists(media_path))

            if has_media and media_path:
                photo_file = FSInputFile(media_path)
                # Ограничение подписи к фото в Telegram - 1024 символов
                if len(text) <= 1024:
                    await self.bot.send_photo(chat_id=target, photo=photo_file, caption=text)
                else:
                    await self.bot.send_photo(chat_id=target, photo=photo_file)
                    await self.bot.send_message(chat_id=target, text=text)
            else:
                # Отправка обычного текстового сообщения
                await self.bot.send_message(chat_id=target, text=text)

            logger.info(f"Post successfully published to {target} (has_media: {has_media})")
            return True

        except Exception as exc:
            # Логируем ошибку, но ОБЯЗАТЕЛЬНО пробрасываем дальше (Fail Fast).
            logger.error(f"Failed to publish to {target}. Error: {exc}")
            raise

        finally:
            # Обязательное закрытие сессии aiohttp во избежание утечек ресурсов
            await self.bot.session.close()