"""Проверка готовности бота (например, перед деплоем или в оркестраторе)."""

from __future__ import annotations

from typing import Any

from aiogram import Bot


async def health_check(bot: Bot) -> dict[str, Any]:
    """
    Вызывает getMe. При успехе возвращает словарь со статусом и данными бота.
    Пробрасывает исключение при невалидном токене или сетевой ошибке.
    """
    me = await bot.get_me()
    return {
        "status": "ok",
        "bot_id": me.id,
        "username": me.username,
        "name": me.full_name,
    }
