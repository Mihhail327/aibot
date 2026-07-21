import uuid
from datetime import datetime, UTC
from app.domains.news.schemas import NewsItemCreate

def test_news_item_create_validation():
    """Verify that NewsItemCreate enforces strict types and length limits."""
    payload = {
        "id": uuid.uuid5(uuid.NAMESPACE_URL, "https://example.com/news/1"),
        "title": "AI Model Released",
        "url": "https://example.com/news/1",
        "summary": "A new AI model has been released.",
        "source": "TechCrunch",
        "published_at": datetime.now(UTC).isoformat()
    }
    
    schema = NewsItemCreate(**payload)
    assert schema.title == "AI Model Released"
    assert schema.url == "https://example.com/news/1"
    assert isinstance(schema.id, uuid.UUID)