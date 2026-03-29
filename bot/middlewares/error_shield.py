"""
Перехват исключений внутри цепочки message/callback: лог + ответ пользователю без падения polling.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

_SAFE = "Произошла ошибка. Попробуйте позже."
_SAFE_DB = "Не удалось сохранить данные. Повторите попытку."


class HandlerErrorShieldMiddleware(BaseMiddleware):
    """Ловит любые исключения из следующего обработчика и не пробрасывает их выше."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            uid = None
            if isinstance(event, Message) and event.from_user:
                uid = event.from_user.id
            elif isinstance(event, CallbackQuery) and event.from_user:
                uid = event.from_user.id
            logger.exception("Handler error user_id=%s type=%s", uid, type(e).__name__)
            reply = _SAFE_DB if isinstance(e, SQLAlchemyError) else _SAFE
            try:
                if isinstance(event, Message):
                    await event.answer(reply)
                elif isinstance(event, CallbackQuery):
                    await event.answer(reply, show_alert=True)
            except Exception:
                logger.exception("Failed to send error reply to user")
            return None
