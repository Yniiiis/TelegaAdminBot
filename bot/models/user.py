"""ORM-модель пользователя бота. user_id — первичный ключ (= уникальность в SQLite)."""

from sqlalchemy import BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class User(Base):
    """Один ряд на Telegram user_id; дубликаты на уровне БД невозможны (PK)."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    get_access_clicked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscription_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
