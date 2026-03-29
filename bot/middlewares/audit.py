"""
Логирование действий пользователей на уровне INFO (без содержимого паролей).
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger("bot.audit")


class UserActionAuditMiddleware(BaseMiddleware):
    """Пишет в лог команды и нажатия inline-кнопок."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            if event.text and event.text.startswith("/"):
                cmd = event.text.split(maxsplit=1)[0]
                logger.info("user_id=%s action=command %s", event.from_user.id, cmd)
        elif isinstance(event, CallbackQuery) and event.from_user and event.data:
            logger.info(
                "user_id=%s action=callback data=%s",
                event.from_user.id,
                event.data,
            )
        return await handler(event, data)
