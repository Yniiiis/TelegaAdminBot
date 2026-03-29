"""
Точка входа: логирование, БД, middleware, graceful shutdown через жизненный цикл диспетчера.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.core.health import health_check
from bot.core.logging import configure_logging
from bot.db.session import init_db
from bot.handlers.admin import router as admin_router
from bot.handlers.errors import register_error_handlers
from bot.handlers.fallback import router as fallback_router
from bot.handlers.start import router as start_router
from bot.middlewares import (
    HandlerErrorShieldMiddleware,
    ThrottlingMiddleware,
    UserActionAuditMiddleware,
)

logger = logging.getLogger(__name__)


def _register_handler_middlewares(dp: Dispatcher) -> None:
    """
    Регистрация слева направо = внешний → внутренний цепочки.
    Вход: throttling → audit → error shield → handler.
    """
    for mw in (
        ThrottlingMiddleware,
        UserActionAuditMiddleware,
        HandlerErrorShieldMiddleware,
    ):
        dp.message.middleware(mw())
        dp.callback_query.middleware(mw())


async def main() -> None:
    configure_logging()
    try:
        await init_db()
    except Exception:
        logger.exception("Не удалось применить миграции БД")
        raise

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    register_error_handlers(dp)
    _register_handler_middlewares(dp)

    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(fallback_router)

    async def on_startup(bot: Bot) -> None:
        try:
            status = await health_check(bot)
            logger.info("Проверка getMe: %s", status)
        except Exception:
            logger.exception("health_check не прошёл — проверьте BOT_TOKEN и сеть")
            raise

    async def on_shutdown() -> None:
        logger.info("Остановка бота (shutdown hook)…")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Старт long polling…")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Polling завершён.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Выход по сигналу пользователя или SystemExit.")
