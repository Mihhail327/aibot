from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class Keyword(Base):
    """SQLAlchemy model representing a keyword for news filtering."""
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Ключевое слово для фильтрации. Уникально, чтобы избежать избыточных проверок в Celery.
    wodr: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)