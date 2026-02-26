"""
DatabaseMiddleware — injects AsyncSession into handler data["db"].
Must be registered FIRST, before UserMiddleware and BanCheckMiddleware.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from loguru import logger

from db.session import async_session_factory


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            logger.debug("[MW:DB] Session opened")
            data["db"] = session
            return await handler(event, data)
