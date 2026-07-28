import logging
from celery import Task
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def run_parsing_task(self: Task, source_url: str) -> dict[str, str]:
    """
    Test background task to verify Celery worker execution.
    """
    logger.info(f"Starting parsing process for: {source_url}")

    try:
        import time
        time.sleep(3)

        logger.info(f"Successfully processed: {source_url}")
        return {"status": "success", "url": source_url}
    
    except Exception as exc:
        logger.error(f"Error processing {source_url}: {exc}")
        raise self.retry(exc=exc, countdown=5)

run_parsing_task.__test__ = False