from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdminSettings(Base):
    """
    Single-row table for storing the maste password hash.
    """
    __tablename__ = "admin_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Хеш единого мастр-пароля
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)