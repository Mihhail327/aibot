from typing import Sequence
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.posts.models import Post, PostStatus
from app.domains.posts.schemas import PostResponse

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/errors", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def get_error_logs(
    session: AsyncSession = Depends(get_db)
) -> Sequence[Post]:
    """
    Retrieve logs for posts that failed generation or publication.
    """
    stmt = select(Post).where(Post.status == PostStatus.FAILED).order_by(Post.updated_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()
