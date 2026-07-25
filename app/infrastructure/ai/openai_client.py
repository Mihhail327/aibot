import logging
from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.infrastructure.ai.interfaces import BaseAIGenerator

logger = logging.getLogger(__name__)


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
        
        # Системный промпт, жестко задающий формат выходных данных (Contract)
        self.system_prompt = (
            "Сделай краткое, интересное описание новости для Telegram-канала. "
            "Обязательно добавь релевантные emoji и call to action в конце. "
            "Не используй Markdown, если он конфликтует с HTML-разметкой Telegram."
        )

    async def generate_post(self, title: str, text: str) -> str:
        """
        Execute the API call to OpenAI.
        
        Raises:
            RuntimeError: If the API call fails or returns empty data.
        """
        user_prompt = f"Заголовок: {title}\n\nТекст новости: {text}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Оптимальный баланс между креативностью и точностью
                max_tokens=1000,
            )
            
            # Извлекаем сгенерированный текст.
            # Type guard для строгого mypy (содержимое может быть None)
            generated_text = response.choices[0].message.content
            if not generated_text:
                raise RuntimeError("OpenAI returned an empty response.")
                
            return generated_text

        except OpenAIError as exc:
            # Нормализация ошибок внешней библиотеки
            logger.error(f"OpenAI API Error: {exc}")
            raise RuntimeError(f"AI Generation failed: {str(exc)}")