"""Валидация пользовательского ввода (без хранения секретов в коде)."""

from __future__ import annotations

# Разумный предел для пароля из чата (Telegram ограничивает длину сообщения).
_MAX_PASSWORD_LEN = 256


def validate_admin_password_input(raw: str | None) -> tuple[str | None, str | None]:
    """
    Возвращает (очищенное значение, None) или (None, текст ошибки).
    Пароль не обрезаем по краям — только проверяем длину.
    """
    if raw is None:
        return None, "Пустой ввод."
    if len(raw) > _MAX_PASSWORD_LEN:
        return None, "Слишком длинная строка."
    return raw, None
