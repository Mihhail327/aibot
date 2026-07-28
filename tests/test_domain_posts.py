import uuid
from datetime import datetime, timezone
from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.domains.posts.models import PostStatus
from app.domains.posts.repository import PostRepository
from app.domains.posts.schemas import PostCreate, PostUpdate
from app.domains.posts.service import PostService
from app.domains.posts.tasks import process_and_publish_post, _async_process_and_publish


@pytest.mark.asyncio
async def test_post_repository_crud(db_session: AsyncSession) -> None:
    repo = PostRepository(db_session)
    news_id = uuid.uuid4()

    # 1. Create
    schema = PostCreate(
        news_id=news_id,
        generated_text="Sleek AI generated text 🔥",
        status=PostStatus.GENERATED
    )
    post = await repo.create(schema)
    assert post.id is not None
    assert post.news_id == news_id
    assert post.generated_text == "Sleek AI generated text 🔥"
    assert post.status == PostStatus.GENERATED

    # 2. Get by ID & Get by News ID & Get by Status
    fetched_by_id = await repo.get_by_id(post.id)
    assert fetched_by_id is not None
    assert fetched_by_id.id == post.id

    fetched_by_news = await repo.get_by_news_id(news_id)
    assert fetched_by_news is not None
    assert fetched_by_news.id == post.id

    generated_posts = await repo.get_by_status(PostStatus.GENERATED, limit=10)
    assert len(generated_posts) == 1

    # 3. Get all
    all_posts = await repo.get_all(skip=0, limit=10)
    assert len(all_posts) == 1

    # 4. Update
    now = datetime.now(timezone.utc)
    updated = await repo.update(post, PostUpdate(status=PostStatus.PUBLISHED, published_at=now))
    assert updated.status == PostStatus.PUBLISHED
    assert updated.published_at is not None

    # 5. Delete
    await repo.delete(updated)
    assert await repo.get_by_id(post.id) is None

@pytest.mark.asyncio
async def test_post_service_business_logic(db_session: AsyncSession) -> None:
    repo = PostRepository(db_session)
    service = PostService(repo)

    news_id1 = uuid.uuid4()
    news_id2 = uuid.uuid4()

    # 1. Create post
    post1 = await service.create_post(PostCreate(
        news_id=news_id1,
        generated_text="AI Post 1",
        status=PostStatus.GENERATED
    ))
    assert post1.news_id == news_id1

    # 2. Duplicate post for same news_id check
    with pytest.raises(DuplicateResourceException):
        await service.create_post(PostCreate(
            news_id=news_id1,
            generated_text="AI Post Duplicate",
            status=PostStatus.NEW
        ))

    # 3. Get missing post
    with pytest.raises(NotFoundException):
        await service.get_post(99999)

    with pytest.raises(NotFoundException):
        await service.get_post_by_news(news_id2)

    # 4. Get by status & list
    by_status = await service.get_posts_by_status(PostStatus.GENERATED)
    assert len(by_status) == 1

    all_p = await service.get_all_posts()
    assert len(all_p) == 1

    # 5. Delete post
    await service.delete_post(post1.id)
    with pytest.raises(NotFoundException):
        await service.get_post(post1.id)

@pytest.mark.asyncio
async def test_posts_api_endpoints(async_client: AsyncClient, auth_headers: dict[str, str], mocker: Any) -> None:
    # Test manual AI generation endpoint
    mock_ai = AsyncMock()
    mock_ai.generate_post.return_value = "Generated Telegram post content 🎉"
    mocker.patch("app.domains.posts.router.OpenAIGenerator", return_value=mock_ai)

    gen_resp = await async_client.post(
        "/api/v1/posts/generate",
        json={"title": "Test Title", "text": "Test text description"},
        headers=auth_headers,
    )
    assert gen_resp.status_code == 200
    assert gen_resp.json()["generated_text"] == "Generated Telegram post content 🎉"

    # Validation failure for empty generate endpoint
    gen_val_resp = await async_client.post(
        "/api/v1/posts/generate",
        json={},
        headers=auth_headers,
    )
    assert gen_val_resp.status_code == 422

    # Create post via API
    news_id = str(uuid.uuid4())
    create_payload = {
        "news_id": news_id,
        "generated_text": "Post via API",
        "status": "generated"
    }
    create_resp = await async_client.post("/api/v1/posts/", json=create_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    post_id = create_resp.json()["id"]

    # List posts
    list_resp = await async_client.get("/api/v1/posts/", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Get single post
    get_resp = await async_client.get(f"/api/v1/posts/{post_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == post_id

    # Get post by news_id
    by_news_resp = await async_client.get(f"/api/v1/posts/news/{news_id}", headers=auth_headers)
    assert by_news_resp.status_code == 200
    assert by_news_resp.json()["id"] == post_id

    # Update post
    patch_resp = await async_client.patch(
        f"/api/v1/posts/{post_id}",
        json={"status": "published"},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "published"

    # Delete post
    del_resp = await async_client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers)
    assert del_resp.status_code == 204

@pytest.mark.asyncio
async def test_async_process_and_publish(db_session: AsyncSession, mocker: Any) -> None:
    news_id = str(uuid.uuid4())
    
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("app.domains.posts.tasks.async_session_maker", return_value=mock_session_ctx)

    mock_ai = AsyncMock()
    mock_ai.generate_post.return_value = "Generated text for task"
    mocker.patch("app.domains.posts.tasks.OpenAIGenerator", return_value=mock_ai)

    mock_pub = AsyncMock()
    mock_pub.send_post.return_value = True
    mocker.patch("app.domains.posts.tasks.TelegramPublisher", return_value=mock_pub)

    task_mock = MagicMock()

    # 1. First run -> creates post and publishes it
    res = await _async_process_and_publish(task_mock, news_id, "Title", "Text")
    assert res is True

    # 2. Second run for same news_id when status is already PUBLISHED -> returns True early
    res_duplicate = await _async_process_and_publish(task_mock, news_id, "Title", "Text")
    assert res_duplicate is True

@pytest.mark.asyncio
async def test_async_process_and_publish_ai_failure(db_session: AsyncSession, mocker: Any) -> None:
    news_id = str(uuid.uuid4())
    
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("app.domains.posts.tasks.async_session_maker", return_value=mock_session_ctx)

    mock_ai = AsyncMock()
    mock_ai.generate_post.side_effect = RuntimeError("OpenAI rate limit")
    mocker.patch("app.domains.posts.tasks.OpenAIGenerator", return_value=mock_ai)

    task_mock = MagicMock()
    task_mock.retry.side_effect = Exception("Celery retry triggered")

    with pytest.raises(Exception) as exc:
        await _async_process_and_publish(task_mock, news_id, "Title", "Text")
    assert "Celery retry triggered" in str(exc.value)

@pytest.mark.asyncio
async def test_async_process_and_publish_telegram_failure(db_session: AsyncSession, mocker: Any) -> None:
    news_id = str(uuid.uuid4())
    
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("app.domains.posts.tasks.async_session_maker", return_value=mock_session_ctx)

    mock_ai = AsyncMock()
    mock_ai.generate_post.return_value = "Generated text"
    mocker.patch("app.domains.posts.tasks.OpenAIGenerator", return_value=mock_ai)

    mock_pub = AsyncMock()
    mock_pub.send_post.return_value = False
    mocker.patch("app.domains.posts.tasks.TelegramPublisher", return_value=mock_pub)

    task_mock = MagicMock()
    task_mock.retry.side_effect = Exception("Celery retry on pub failure")

    with pytest.raises(Exception) as exc:
        await _async_process_and_publish(task_mock, news_id, "Title", "Text")
    assert "Celery retry on pub failure" in str(exc.value)

def test_process_and_publish_post_task(mocker: Any) -> None:
    mocker.patch("app.domains.posts.tasks._async_process_and_publish", return_value=True)
    res = process_and_publish_post("123", "Title", "Text")
    assert res is True
