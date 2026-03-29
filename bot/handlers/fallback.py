"""
Сообщения, не обработанные другими роутерами (без краша и лишнего шума).
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

router = Router(name="fallback")
logger = logging.getLogger(__name__)


@router.callback_query()
async def unknown_callback(callback: CallbackQuery) -> None:
    logger.info(
        "Unknown callback user_id=%s data=%s",
        callback.from_user.id if callback.from_user else None,
        callback.data,
    )
    await callback.answer("Действие устарело или неизвестно. Откройте /start.", show_alert=True)


@router.message(~Command())
async def unknown_message(message: Message) -> None:
    logger.info(
        "Unhandled message user_id=%s content_type=%s",
        message.from_user.id if message.from_user else None,
        message.content_type,
    )
    await message.answer(
        "Команда не распознана. Нажмите /start, чтобы открыть меню."
    )
