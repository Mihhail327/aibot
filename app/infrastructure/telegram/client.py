import logging
from typing import Any

from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger(__name__)


class TelegramParserClient:
    """
    Wrapper for Telethon MTProto clinet used exclusively for channel parsing.
    Requires an active StringSession to avoid SQLite database locks in Celery/Docker environments.
    """

    def __init__(self, api_id: int, api_hash: str, session_string: str) -> None:
        """
        Initialize the Telegram MTProto client.

        Args:
            api_id (int): Telegram API ID from my.telegram.org.
            api_hash (str): Telegram API Hash.
            session_string (str): Base64 encoded Telethon string session.
        """
        # Защита от запуска без конфигурации
        if not api_id or not api_hash or not session_string:
            raise ValueError("Telegram API credential (ID, HASH, SESSION) must be provided")

        # Используем StringSession для безопасной работы в мультипроцессорной среде
        self._session = StringSession(session_string)
        self.client = TelegramClient(
            session=self._session,
            api_id=api_id,
            api_hash=api_hash,
            # Отключаем дефолтные логи Telethon, чтобы они не спамили в stdout
            base_logger=logging.getLogger("telethon_base"),
        )

    async def start(self) -> None:
        """
        Connect to Telegram servers and verify authorization state.
        Raises ValueError if the session is unauthorized.
        """
        # Подключаем к серверам (MTProto)
        await self.client.connect()

        # Проверяем валидность переданной сессии
        if not await self.client.is_user_authorized():
            logger.error("Telegram MTProto client is not authorized. Session string is invalid.")
            raise ValueError("Unauthorized Telegram session. Please generate a new StringSession.")

        logger.info("Telegram MTProto client successfully connected and authorized.")

    async def stop(self) -> None:
        """Safely disconnect the client from Telegram servers."""
        if self.client.is_connected():
            # Добавляем игнорирование для метода disconnect
            await self.client.disconnect()  # type: ignore
            logger.info("Telegram MTProto client disconnected.")

    async def __aenter__(self) -> "TelegramParserClient":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()