"""
BanCheckMiddleware — blocks banned users.
Must be registered AFTER UserMiddleware (uses data["user"]).
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from loguru import logger


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        if user and user.is_banned:
            logger.warning(f"[MW:BAN] Blocked user {user.id}")
            # Send notification to banned user
            if isinstance(event, Update):
                if event.message:
                    await event.message.answer("⛔ Вы заблокированы. Обратитесь к администратору.")
                elif event.callback_query:
                    await event.callback_query.answer("⛔ Вы заблокированы.", show_alert=True)
            return  # Stop chain — don't call handler

        return await handler(event, data)
