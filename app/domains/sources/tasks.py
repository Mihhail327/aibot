import logging
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def test_parsing_task(self, source_url: str) -> dict[str, str]:
    """
    Test background task to verify Celery worker execution.
    
    Args:
        source_url (str): The URL of the source to process.
        
    Returns:
        dict[str, str]: Status of the execution.
    """
    # Логируем старт задачи (в production здесь будет Telethon/requests)
    logger.info(f"Starting parsing process for: {source_url}")

    try:
        # Эмуляция блокирующей I/O операции (например, парсинг сайта)
        import time
        time.sleep(3)

        logger.info(f"Successfully processed: {source_url}")
        return {"status": "success", "url": source_url}
    
    except Exception as exc:
        # Логируем ошибку и отправляем задачу на повторное выполнение
        logger.error(f"Error processing {source_url}: {exc}")
        raise self.retry(exc=exc, countdown=5)