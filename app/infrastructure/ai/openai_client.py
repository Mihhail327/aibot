import html
import re
import logging
from typing import Any
from openai import AsyncOpenAI, OpenAIError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.infrastructure.ai.interfaces import BaseAIGenerator

logger = logging.getLogger(__name__)


def _markdown_to_telegram_html(text: str) -> str:
    """Convert basic Markdown syntax (**bold**, [link](url)) to Telegram-compatible HTML tags."""
    # Экранируем спецсимволы HTML
    escaped_text = html.escape(text)
    # Заменяем ссылки [label](url) на <a href="url">label</a>
    escaped_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', escaped_text)
    # Заменяем **жирный** на <b>жирный</b>
    escaped_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', escaped_text)
    return escaped_text


def _should_retry_openai(exc: BaseException) -> bool:
    """Retry on transient OpenAI errors, excluding quota issues."""
    return isinstance(exc, OpenAIError) and "insufficient_quota" not in str(exc)


class OpenAIGenerator(BaseAIGenerator):
    """
    OpenAI-specific implementation of the AI generator.
    Handles authentication, prompting, and error normalization.
    """

    def __init__(self) -> None:
        """Initialize the async OpenAI client."""
        # Инициализация официального клиента с ключом из конфигурации
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )
        # Выбор модели. gpt-4o-mini оптимален по соотношению цена/качество
        self.model = "gpt-4o-mini"
        
        # Системный промпт, жестко задающий формат выходных данных в Telegram HTML
        self.system_prompt = (
            "Сделай краткое, интересное описание новости для Telegram-канала. "
            "Используй только HTML-разметку Telegram (<b>жирный</b>, <i>курсив</i>, <a href='url'>текст</a>). "
            "НЕ используй Markdown (не используй ** и [текст](url)). "
            "Обязательно добавь релевантные emoji и call to action в конце."
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_should_retry_openai),
        reraise=True,
    )
    async def _call_openai_api(self, user_prompt: str) -> Any:
        """Execute OpenAI API completion with automatic exponential backoff retries."""
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )

    async def generate_post(self, title: str, text: str) -> str:
        """
        Execute the API call to OpenAI.
        
        Raises:
            RuntimeError: If the API call fails or returns empty data.
        """
        user_prompt = f"Заголовок: {title}\n\nТекст новости: {text}"
        
        try:
            response = await self._call_openai_api(user_prompt)
            
            # Извлекаем сгенерированный текст.
            generated_text = response.choices[0].message.content
            if not generated_text:
                raise RuntimeError("OpenAI returned an empty response.")
                
            return str(generated_text)

        except OpenAIError as exc:
            logger.error(f"OpenAI API Error: {exc}")
            
            # Если закончилась квота (429), используем красивый HTML fallback
            if "insufficient_quota" in str(exc):
                logger.warning("OpenAI quota exceeded. Using fallback HTML text generator.")
                clean_title = html.escape(title.replace("**", "").strip())
                formatted_text = _markdown_to_telegram_html(text)
                return f"📌 <b>{clean_title}</b>\n\n{formatted_text}"
                
            raise RuntimeError(f"AI Generation failed: {str(exc)}")