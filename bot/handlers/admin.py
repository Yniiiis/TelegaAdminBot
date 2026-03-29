"""
Админ-вход по паролю (FSM). Опционально — белый список user_id в .env.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.config import ADMIN_PASSWORD, ADMIN_USER_IDS
from bot.services import admin_service
from bot.utils.validation import validate_admin_password_input

router = Router(name="admin")
logger = logging.getLogger(__name__)


class AdminAuth(StatesGroup):
    waiting_password = State()


def _admin_allowed(user_id: int) -> bool:
    if not ADMIN_USER_IDS:
        return True
    return user_id in ADMIN_USER_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not ADMIN_PASSWORD:
        await message.answer("Админ-панель отключена: в .env не задан ADMIN_PASSWORD.")
        return
    uid = message.from_user.id if message.from_user else 0
    if not _admin_allowed(uid):
        logger.warning("Rejected /admin from unauthorized user_id=%s", uid)
        await message.answer("Команда недоступна.")
        return
    await state.set_state(AdminAuth.waiting_password)
    await message.answer(
        "Введите пароль администратора.\n"
        "Отправьте /cancel для отмены."
    )


@router.message(Command("cancel"), StateFilter(AdminAuth.waiting_password))
async def admin_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Вход в админ-панель отменён.")
    logger.info("Admin login cancelled user_id=%s", message.from_user.id)


@router.message(StateFilter(AdminAuth.waiting_password), F.text, ~Command())
async def admin_password_received(message: Message, state: FSMContext) -> None:
    if not ADMIN_PASSWORD:
        await state.clear()
        return
    uid = message.from_user.id
    if not _admin_allowed(uid):
        await state.clear()
        logger.warning("Password attempt from non-whitelisted user_id=%s", uid)
        await message.answer("Команда недоступна.")
        return

    raw = message.text or ""
    cleaned, err = validate_admin_password_input(raw)
    if err:
        await message.answer(err)
        return

    assert cleaned is not None
    ok = admin_service.verify_admin_password(cleaned)
    await state.clear()
    if ok:
        logger.info("Admin login success user_id=%s", uid)
        text = await admin_service.build_admin_dashboard_text()
        await message.answer(text)
    else:
        logger.warning("Admin login failed (wrong password) user_id=%s", uid)
        await message.answer("Неверный пароль.")


@router.message(StateFilter(AdminAuth.waiting_password))
async def admin_password_not_text(message: Message) -> None:
    await message.answer(
        "Отправьте пароль текстовым сообщением или /cancel для отмены."
    )
