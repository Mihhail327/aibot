from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    """Base contract for all custom business exceptions.
    
    A global exception handler in main.py will catch these automatically.
    """
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        # Инициализируем базовый класс FastAPI HTTPException
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(BaseAPIException):
    """Raised when a resource (source, news) is not found in the database."""
    def __init__(self, detail: str = "Resource not found.") -> None:
        # 404 статус код для отсутствующих записей
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class DuplicateResourceException(BaseAPIException):
    """Ensures data integrity. Raised upon resource duplication (e.g., identical URL)."""
    def __init__(self, detail: str = "Resource already exists.") -> None:
        # 409 статус код для конфликта уникальных ограничений (Unique Constraints)
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class ExternalServiceException(BaseAPIException):
    """Raised when an external API (OpenAI, Telegram) fails or times out."""
    def __init__(self, detail: str = "External service integration error.") -> None:
        # 502 статус код, так как наш сервер выступает шлюзом (Gateway) к чужому API
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)