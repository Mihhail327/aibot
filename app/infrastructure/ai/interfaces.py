from abc import ABC, abstractmethod


class BaseAIGenerator(ABC):
    """
    Abstract contract for AI text generation.
    Ensures that any LLM provider implements this exact interface.
    """

    @abstractmethod
    async def generate_post(self, title: str, text: str) -> str:
        """
        Generate a localized, formatting-ready post for Telegram.
        
        Args:
            title: The original news title.
            text: The original news content or summary.
            
        Returns:
            str: The generated text ready for publication.
        """
        pass