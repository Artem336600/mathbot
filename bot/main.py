"""
MathTrainer bot — entry point.
Registers middlewares (DB → User → Ban) and all routers, starts polling.
"""
import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

from bot.config import settings
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.user import UserMiddleware
from bot.middlewares.ban_check import BanCheckMiddleware


def setup_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    logger.info(f"[BOOT] Log level: {settings.log_level}")


def register_routers(dp: Dispatcher) -> None:
    """Register all feature routers. Import here to avoid circular imports."""
    from bot.handlers.start import router as start_router
    from bot.handlers.sprint import router as sprint_router
    from bot.handlers.training import router as training_router
    from bot.handlers.topics import router as topics_router
    from bot.handlers.mistakes import router as mistakes_router
    from bot.handlers.profile import router as profile_router
    from bot.handlers.admin.menu import router as admin_menu_router
    from bot.handlers.admin.content import router as admin_content_router
    from bot.handlers.admin.broadcast import router as admin_broadcast_router

    dp.include_router(start_router)
    dp.include_router(sprint_router)
    dp.include_router(training_router)
    dp.include_router(topics_router)
    dp.include_router(mistakes_router)
    dp.include_router(profile_router)
    dp.include_router(admin_menu_router)
    dp.include_router(admin_content_router)
    dp.include_router(admin_broadcast_router)
    logger.info("[BOOT] All routers registered")


async def on_startup(bot: Bot) -> None:
    logger.info("[BOOT] Starting MathTrainer bot...")

    # Run DB migrations
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("[BOOT] DB migrated to head")
    except Exception as e:
        logger.error(f"[BOOT] Alembic migration failed: {e}")

    # Check Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        logger.info("[BOOT] Redis connected")
    except Exception as e:
        logger.warning(f"[BOOT] Redis connection failed: {e}")


async def on_shutdown(bot: Bot) -> None:
    logger.info("[BOOT] Shutting down bot...")


async def main() -> None:
    setup_logging()

    bot = Bot(token=settings.bot_token)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Register middlewares in correct order
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())
    dp.update.middleware(BanCheckMiddleware())
    logger.debug("[BOOT] Middlewares registered: DB → User → Ban")

    # Register routers
    register_routers(dp)

    # Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Global error handler
    @dp.errors()
    async def global_error_handler(event, exception):
        logger.exception(f"[ERROR] Unhandled exception: {exception}")
        try:
            if event.update.message:
                await event.update.message.answer(
                    "❗ Произошла ошибка. Попробуйте ещё раз или вернитесь в /start"
                )
            elif event.update.callback_query:
                await event.update.callback_query.answer(
                    "❗ Произошла ошибка.", show_alert=True
                )
        except Exception:
            pass
        return True

    logger.info(f"[BOOT] Config loaded: db={settings.database_url[:30]}...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
