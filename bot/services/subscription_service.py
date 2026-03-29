"""
Проверка подписки на канал с разбором типичных ошибок Telegram API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramNotFound,
    TelegramServerError,
)
from aiogram.types import (
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)

logger = logging.getLogger(__name__)

_SUBSCRIBED_TYPES = (
    ChatMemberMember,
    ChatMemberAdministrator,
    ChatMemberOwner,
    ChatMemberRestricted,
)

_ACTIVE_STATUSES = frozenset(
    {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.RESTRICTED,
    }
)


def is_subscribed_member(member: object) -> bool:
    """
    Считаем подписанным: member / administrator / creator / restricted.
    Сначала isinstance (быстро), затем по полю status — если Telegram/aiogram
    вернёт вариант, который мы не перечислили в isinstance, всё равно распознаем.
    """
    if isinstance(member, _SUBSCRIBED_TYPES):
        return True
    status = getattr(member, "status", None)
    if status is None:
        return False
    if isinstance(status, ChatMemberStatus):
        return status in _ACTIVE_STATUSES
    if isinstance(status, str):
        try:
            return ChatMemberStatus(status) in _ACTIVE_STATUSES
        except ValueError:
            return status in {"member", "administrator", "creator", "restricted"}
    return False


@dataclass(frozen=True)
class SubscriptionCheckResult:
    """
    definitive: получен ответ API о членстве (успех или «не подписан»).
    Если False — сбой запроса, нужно показать alert_text.
    """

    definitive: bool
    subscribed: bool
    alert_text: str
    log_detail: str


def _bad_request_classification(raw: str) -> SubscriptionCheckResult | None:
    """Возвращает результат, если текст ошибки известен; иначе None."""

    if "chat not found" in raw or "member not found" in raw:
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text="Канал недоступен. Убедитесь, что username или id указаны верно.",
            log_detail="bad_request_chat",
        )

    # Нет прав у бота / чат недоступен для метода (часто приходит как 400, не Forbidden).
    if any(
        x in raw
        for x in (
            "not enough rights",
            "need administrator",
            "administrator rights",
            "chat_admin_required",
            "rights are required",
            "method is available only for",
            "member list is inaccessible",
            "can't get chat member",
        )
    ):
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text=(
                "Бот не может проверить подписку: добавьте его в канал администратором "
                "(желательно с правом «добавлять участников» / просмотр участников)."
            ),
            log_detail="bad_request_rights",
        )

    if "user not found" in raw:
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text="Не удалось проверить подписку для аккаунта. Попробуйте позже.",
            log_detail="bad_request_user",
        )

    # Некоторые клиенты/версии API отдают отказ участия как 400.
    if any(
        x in raw
        for x in (
            "user_not_participant",
            "not a participant",
            "participant_id_invalid",
            "user is not a member",
        )
    ):
        return SubscriptionCheckResult(
            definitive=True,
            subscribed=False,
            alert_text="",
            log_detail="bad_request_not_participant",
        )

    return None


async def check_channel_subscription(bot: Bot, chat_id: str | int, user_id: int) -> SubscriptionCheckResult:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        sub = is_subscribed_member(member)
        return SubscriptionCheckResult(
            definitive=True,
            subscribed=sub,
            alert_text="",
            log_detail="ok",
        )
    except TelegramForbiddenError as e:
        logger.error("Subscription check forbidden (bot rights?): %s", e)
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text=(
                "Бот не может проверить подписку: добавьте его администратором канала "
                "с правом просматривать участников."
            ),
            log_detail="forbidden",
        )
    except TelegramNotFound as e:
        logger.error("Channel not found for subscription check: %s", e)
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text="Канал не найден. Проверьте настройку TELEGRAM_CHANNEL в .env.",
            log_detail="not_found",
        )
    except TelegramBadRequest as e:
        raw = (e.message or str(e)).lower()
        logger.warning("BadRequest on get_chat_member user_id=%s raw=%r", user_id, raw)
        classified = _bad_request_classification(raw)
        if classified is not None:
            return classified
        logger.error("Unclassified BadRequest get_chat_member user_id=%s: %s", user_id, e)
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text="Не удалось выполнить проверку. Попробуйте позже.",
            log_detail="bad_request_other",
        )
    except (TelegramNetworkError, TelegramServerError) as e:
        logger.error("Network/server error on get_chat_member: %s", e)
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text="Сеть Telegram временно недоступна. Повторите через минуту.",
            log_detail="network",
        )
    except TelegramAPIError as e:
        logger.error("Telegram API error on get_chat_member: %s", e)
        return SubscriptionCheckResult(
            definitive=False,
            subscribed=False,
            alert_text="Сервис Telegram вернул ошибку. Попробуйте позже.",
            log_detail="api_other",
        )
