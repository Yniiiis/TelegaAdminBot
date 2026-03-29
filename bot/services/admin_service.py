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
        "Доступ разрешён.\n\n"
        "📊 Статистика:\n"
        f"• Всего пользователей: {total}\n"
        f"• Нажали «Get Access»: {access}\n"
        f"• Прошли проверку подписки: {passed}"
    )
