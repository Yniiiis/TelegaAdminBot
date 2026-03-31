"""Проверка пароля админки и сборка текста дашборда (без логирования секретов)."""

import secrets

from bot.config import ADMIN_PASSWORD
from bot.services import user_service


def verify_admin_password(entered: str) -> bool:
    if not ADMIN_PASSWORD:
        return False
    return secrets.compare_digest(entered, ADMIN_PASSWORD)


async def build_admin_dashboard_text() -> str:
    total, access, passed = await user_service.get_admin_statistics()
    return (
        "Доступ в админ-панель открыт.\n\n"
        "📊 Статистика бота (уникальные пользователи по Telegram ID):\n\n"
        f"• Запускали бота (/start): {total}\n"
        "  └ сколько разных людей нажали «Старт» и попали в базу.\n\n"
        f"• Перешли к шагу с каналом (кнопка «Перейти к музыке ✅»): {access}\n"
        "  └ сколько человек нажали эту кнопку (каждый считается один раз).\n\n"
        f"• Подтвердили подписку на канал (кнопка «Проверить подписку 🔎»): {passed}\n"
        "  └ сколько человек успешно прошли проверку «я подписан» (каждый — один раз)."
    )
