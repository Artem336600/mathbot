"""
UserMiddleware — fetches or creates User from DB, injects into data["user"].
Must be registered AFTER DatabaseMiddleware.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from loguru import logger

from repositories.user_repo import UserRepository


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        db = data.get("db")
        if db is None:
            return await handler(event, data)

        # Extract Telegram user from event
        tg_user = None
        if isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        if tg_user is None:
            return await handler(event, data)

        user = await UserRepository.get_or_create(
            tg_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name or "",
            db=db,
        )
        logger.debug(f"[MW:User] User {tg_user.id} fetched/created: level={user.level}")
        data["user"] = user
        return await handler(event, data)
