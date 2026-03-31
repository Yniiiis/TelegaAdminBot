from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import get_channel_subscribe_url


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к музыке ✅", callback_data="get_access")],
        ]
    )


def subscribe_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    url = get_channel_subscribe_url()
    if url:
        rows.append([InlineKeyboardButton(text="Подписаться ✅", url=url)])
    rows.append([InlineKeyboardButton(text="Проверить подписку 🔎", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
