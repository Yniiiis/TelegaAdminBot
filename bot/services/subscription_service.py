"""
Проверка подписки на канал с разбором типичных ошибок Telegram API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
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


def is_subscribed_member(member: object) -> bool:
    return isinstance(member, _SUBSCRIBED_TYPES)


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
        logger.warning("BadRequest on get_chat_member user_id=%s: %s", user_id, e)
        if "chat not found" in raw or "member not found" in raw:
            return SubscriptionCheckResult(
                definitive=False,
                subscribed=False,
                alert_text="Канал недоступен. Убедитесь, что username или id указаны верно.",
                log_detail="bad_request_chat",
            )
        if "user not found" in raw:
            return SubscriptionCheckResult(
                definitive=False,
                subscribed=False,
                alert_text="Не удалось проверить подписку для аккаунта. Попробуйте позже.",
                log_detail="bad_request_user",
            )
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
