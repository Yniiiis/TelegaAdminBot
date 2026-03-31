"""
Обработчики /start, доступа к каналу и проверки подписки.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.config import CHANNEL_CHAT_ID
from bot.keyboards.inline import start_keyboard, subscribe_keyboard
from bot.services import subscription_service, user_service
from bot.utils.telegram_messages import edit_or_answer

router = Router(name="start")
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Добро пожаловать в OFFRKN Music.\n\n"
    "Здесь музыка звучит без цензуры и без лишних ограничений: полные версии треков, "
    "любимые артисты и рекомендации, которые подстраиваются под твой вкус.\n\n"
    "Открывай новое и слушай музыку так, как она должна звучать."
)

SUBSCRIBE_PROMPT = (
    "Чтобы получить доступ, подпишитесь на наш Telegram-канал — там будут публиковаться "
    "анонсы важных обновлений о работе нашего сервиса."
)

SUBSCRIPTION_SUCCESS = "✅ Доступ открыт. Спасибо за подписку на канал!"

SUBSCRIPTION_REQUIRED = (
    "Подписка на канал не найдена. Оформите подписку через кнопку ниже и нажмите "
    "«Проверить подписку 🔎» ещё раз."
)

_EMPTY_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[])


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        logger.warning("/start без from_user (канал/аноним)")
        return
    await user_service.register_user_if_new(message.from_user.id)
    await message.answer(WELCOME_TEXT, reply_markup=start_keyboard())


@router.callback_query(F.data == "get_access")
async def callback_get_access(callback: CallbackQuery) -> None:
    await callback.answer()
    await user_service.record_get_access_click(callback.from_user.id)
    if callback.message:
        await edit_or_answer(callback, SUBSCRIBE_PROMPT, reply_markup=subscribe_keyboard())


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery) -> None:
    if not CHANNEL_CHAT_ID:
        await callback.answer(
            "Канал не настроен (TELEGRAM_CHANNEL в .env).",
            show_alert=True,
        )
        return

    result = await subscription_service.check_channel_subscription(
        callback.bot,
        CHANNEL_CHAT_ID,
        callback.from_user.id,
    )

    if not result.definitive:
        logger.warning(
            "Subscription check inconclusive user_id=%s detail=%s",
            callback.from_user.id,
            result.log_detail,
        )
        await callback.answer(result.alert_text, show_alert=True)
        return

    await callback.answer()

    if not callback.message:
        logger.warning("check_subscription: no message user_id=%s", callback.from_user.id)
        return

    if result.subscribed:
        await user_service.record_subscription_passed_once(callback.from_user.id)
        await edit_or_answer(callback, SUBSCRIPTION_SUCCESS, reply_markup=_EMPTY_KEYBOARD)
    else:
        await edit_or_answer(callback, SUBSCRIPTION_REQUIRED, reply_markup=subscribe_keyboard())
