"""
Глобальные ошибки вне цепочки message/callback (или если исключение не перехвачен щитом).
"""

from __future__ import annotations

import logging

from aiogram import Dispatcher
from aiogram.types import ErrorEvent, Message, Update
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

_GENERIC_USER_TEXT = "Произошла ошибка. Попробуйте позже."
_DB_USER_TEXT = "Не удалось сохранить данные. Повторите попытку."


def _extract_message(update: Update) -> Message | None:
    if update.message:
        return update.message
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    return None


def _user_id_from_update(update: Update) -> int | None:
    if update.message and update.message.from_user:
        return update.message.from_user.id
    if update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user.id
    return None


def register_error_handlers(dp: Dispatcher) -> None:
    @dp.errors()
    async def global_error_handler(event: ErrorEvent) -> bool:
        exc = event.exception
        uid = _user_id_from_update(event.update)
        logger.error(
            "Global error handler: user_id=%s exc_type=%s: %s",
            uid,
            type(exc).__name__,
            exc,
            exc_info=exc,
        )

        target = _extract_message(event.update)
        if target is not None:
            text = _DB_USER_TEXT if isinstance(exc, SQLAlchemyError) else _GENERIC_USER_TEXT
            try:
                await target.answer(text)
            except Exception:
                logger.exception("Could not deliver error message to user user_id=%s", uid)

        return True
