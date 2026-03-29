"""
Операции с пользователями: транзакции, повтор при временных сбоях БД, защита от гонок.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.exc import IntegrityError, OperationalError

from bot.config import DB_RETRY_ATTEMPTS, DB_RETRY_DELAY_SEC
from bot.db.repositories.user_repository import UserRepository
from bot.db.session import async_session_maker

logger = logging.getLogger(__name__)


async def _run_db_with_retry(operation_name: str, user_id: int | None, work) -> None:
    """Выполняет async work() с повтором при OperationalError; гасит IntegrityError (гонка вставки)."""
    last_exc: Exception | None = None
    for attempt in range(DB_RETRY_ATTEMPTS):
        try:
            await work()
            return
        except IntegrityError:
            logger.warning(
                "DB IntegrityError in %s user_id=%s (вероятная гонка вставки)",
                operation_name,
                user_id,
            )
            return
        except OperationalError as e:
            last_exc = e
            logger.warning(
                "DB OperationalError %s attempt %s/%s: %s",
                operation_name,
                attempt + 1,
                DB_RETRY_ATTEMPTS,
                e,
            )
            await asyncio.sleep(DB_RETRY_DELAY_SEC * (attempt + 1))
    logger.error("DB operation %s failed after retries user_id=%s", operation_name, user_id)
    if last_exc:
        raise last_exc


async def register_user_if_new(user_id: int) -> None:
    async def work() -> None:
        async with async_session_maker() as session:
            try:
                repo = UserRepository(session)
                if await repo.ensure_user(user_id):
                    await session.commit()
                    logger.info("User registered user_id=%s", user_id)
            except (OperationalError, IntegrityError):
                await session.rollback()
                raise

    await _run_db_with_retry("register_user_if_new", user_id, work)


async def record_get_access_click(user_id: int) -> None:
    async def work() -> None:
        async with async_session_maker() as session:
            try:
                repo = UserRepository(session)
                if await repo.record_get_access_unique(user_id):
                    await session.commit()
                    logger.info("Unique Get Access recorded user_id=%s", user_id)
            except (OperationalError, IntegrityError):
                await session.rollback()
                raise

    await _run_db_with_retry("record_get_access_click", user_id, work)


async def record_subscription_passed_once(user_id: int) -> bool:
    """True, если впервые отмечена успешная проверка подписки."""

    recorded = False

    async def work() -> None:
        nonlocal recorded
        async with async_session_maker() as session:
            try:
                repo = UserRepository(session)
                if await repo.record_subscription_passed_unique(user_id):
                    await session.commit()
                    recorded = True
                    logger.info("Unique subscription check recorded user_id=%s", user_id)
            except (OperationalError, IntegrityError):
                await session.rollback()
                raise

    await _run_db_with_retry("record_subscription_passed_once", user_id, work)
    return recorded


async def get_admin_statistics() -> tuple[int, int, int]:
    async def work() -> tuple[int, int, int]:
        async with async_session_maker() as session:
            repo = UserRepository(session)
            return await repo.get_admin_statistics()

    last_exc: Exception | None = None
    for attempt in range(DB_RETRY_ATTEMPTS):
        try:
            return await work()
        except OperationalError as e:
            last_exc = e
            logger.warning(
                "get_admin_statistics OperationalError attempt %s/%s: %s",
                attempt + 1,
                DB_RETRY_ATTEMPTS,
                e,
            )
            await asyncio.sleep(DB_RETRY_DELAY_SEC * (attempt + 1))
    if last_exc:
        raise last_exc
    return 0, 0, 0
