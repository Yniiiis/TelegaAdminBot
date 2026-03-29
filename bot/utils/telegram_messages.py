"""Безопасное редактирование сообщений Telegram с запасным вариантом answer."""

from __future__ import annotations

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


async def edit_or_answer(
    callback: CallbackQuery,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message | None:
    """
    Пытается отредактировать текст сообщения колбэка; при ошибке — новое сообщение.
    Избегает дублирования, когда редактирование возможно.
    """
    msg = callback.message
    if msg is None:
        return None
    try:
        await msg.edit_text(text, reply_markup=reply_markup)
        return msg
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "message is not modified" in err:
            return msg
        logger.info("edit_text fallback to answer: %s", e)
        return await msg.answer(text, reply_markup=reply_markup)
    except Exception:
        logger.exception("edit_or_answer failed")
        return await msg.answer(text, reply_markup=reply_markup)
