"""
Сообщения, не обработанные другими роутерами (без краша и лишнего шума).
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

router = Router(name="fallback")
logger = logging.getLogger(__name__)


class _NotLeadingSlashCommandFilter(BaseFilter):
    """
    aiogram 3: ~Command() без списка команд падает при импорте.
    Пропускаем медиа и текст без ведущего «/»; команды вида /foo не трогаем здесь.
    """

    async def __call__(self, message: Message) -> bool:
        text = message.text
        if text is None:
            return True
        return not text.startswith("/")


@router.callback_query()
async def unknown_callback(callback: CallbackQuery) -> None:
    logger.info(
        "Unknown callback user_id=%s data=%s",
        callback.from_user.id if callback.from_user else None,
        callback.data,
    )
    await callback.answer("Действие устарело или неизвестно. Откройте /start.", show_alert=True)


@router.message(_NotLeadingSlashCommandFilter())
async def unknown_message(message: Message) -> None:
    logger.info(
        "Unhandled message user_id=%s content_type=%s",
        message.from_user.id if message.from_user else None,
        message.content_type,
    )
    await message.answer(
        "Команда не распознана. Нажмите /start, чтобы открыть меню."
    )
