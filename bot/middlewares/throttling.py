"""
Ограничение частоты запросов на пользователя (in-memory).
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import (
    CHECK_SUB_COOLDOWN_SEC,
    GET_ACCESS_COOLDOWN_SEC,
    RATE_MAX_EVENTS,
    RATE_WINDOW_SEC,
)
from bot.utils.rate_limit import UserRateLimiter

logger = logging.getLogger(__name__)

_limiter = UserRateLimiter(window_sec=RATE_WINDOW_SEC, max_events=RATE_MAX_EVENTS)


class ThrottlingMiddleware(BaseMiddleware):
    """Общий лимит событий + cooldown на отдельные callback."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _user_id(event)
        if user_id is None:
            return await handler(event, data)

        if not await _limiter.allow_general(user_id):
            logger.warning("Rate limit exceeded user_id=%s", user_id)
            await _notify_throttled(event)
            return None

        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            wait = await _limiter.cooldown_remaining(
                user_id, "check_sub", CHECK_SUB_COOLDOWN_SEC
            )
            if wait > 0:
                logger.info("Check subscription cooldown user_id=%s wait=%.1fs", user_id, wait)
                try:
                    await event.answer(
                        f"Подождите ещё {wait:.0f} с перед следующей проверкой.",
                        show_alert=True,
                    )
                except Exception:
                    logger.exception("callback.answer failed (cooldown)")
                return None

        if isinstance(event, CallbackQuery) and event.data == "get_access":
            wait = await _limiter.cooldown_remaining(
                user_id, "get_access", GET_ACCESS_COOLDOWN_SEC
            )
            if wait > 0:
                try:
                    await event.answer(
                        f"Не так часто. Через {wait:.0f} с.",
                        show_alert=True,
                    )
                except Exception:
                    logger.exception("callback.answer failed (get_access cd)")
                return None

        return await handler(event, data)


def _user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    return None


async def _notify_throttled(event: TelegramObject) -> None:
    text = "Слишком много запросов. Подождите немного."
    try:
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
    except Exception:
        logger.exception("throttle notify failed")
