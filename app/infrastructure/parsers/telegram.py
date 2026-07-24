import logging
from typing import Sequence

# Импортируем тип Message из Telethon для строгой типизации
from telethon.tl.custom.message import Message

from app.infrastructure.telegram.client import TelegramParserClient

logger = logging.getLogger(__name__)


class TelegramChannelParser:
    """Service for extracting and filtering messages from Telegram channels."""

    def __init__(self, parser_client: TelegramParserClient) -> None:
        """
        Initialize the parser with an active MTProto client.
        """
        self.client_wrapper = parser_client

    async def fetch_recent_messages(self, channel_username: str, limit: int = 20) -> list[Message]:
        """
        Fetch the latest text-containig messages from a specific channel.
        """
        messages: list[Message] = []
        try:
            # client.iter_messages - асинхронный генератор Telethon
            async for message in self.client_wrapper.client.iter_messages(channel_username, limit=limit):
                if message.text: # Отсеиваем системные сообщения и медиа без подписки
                    messages.append(message)
        except Exception as e:
            # Логируем ошибку, но не роняем весь процесс (Graceful degradation)
            logger.error(f"Failed to fetch messages from '{channel_username}': {e}")

        return messages

    def filter_by_keywords(self, messages: list[Message], keywords: Sequence[str]) -> list[Message]:
        """
        Filter messages, keeping only those that contain at least one target keyword.
        """
        if not keywords:
            # Если ключевых слов нет, считаем, что фильтрация не требуется
            return messages

        filtered_messages: list[Message] = []
        # Приводим слова к нижнему регистру один раз перед циклом для оптимизации (0(N))
        normalized_keywords = [k.lower() for k in keywords]

        for msg in messages:
            if not msg.text:
                continue

            text_lower = msg.text.lower()
            # Проевряем вхождение хотя бы одного ключевого слова (substring match)
            if any(keyword in text_lower for keyword in normalized_keywords):
                filtered_messages.append(msg)

        return filtered_messages