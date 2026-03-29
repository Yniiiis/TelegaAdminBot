import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import DATABASE_URL
from bot.db.base import Base
from bot.models.user import User  # noqa: F401

logger = logging.getLogger(__name__)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _run_alembic_upgrade() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    cfg = Config(str(root / "alembic.ini"))
    logger.info("Применение миграций Alembic…")
    command.upgrade(cfg, "head")
    logger.info("Миграции применены.")


async def init_db() -> None:
    await asyncio.to_thread(_run_alembic_upgrade)
