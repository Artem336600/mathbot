"""
Broadcast service — send message to all non-banned users.
No Aiogram imports in function signatures except Bot type hint.
"""
import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repo import UserRepository


async def send_to_all(text: str, bot, db: AsyncSession) -> dict:
    """
    Send text message to all active users.
    Returns: {"sent": int, "failed": int}
    """
    user_ids = await UserRepository.get_all_ids(db)
    total = len(user_ids)
    sent = 0
    failed = 0

    logger.info(f"[SVC:Broadcast] Starting broadcast to {total} users")

    for i, user_id in enumerate(user_ids, 1):
        try:
            await bot.send_message(chat_id=user_id, text=text)
            sent += 1
        except Exception as e:
            # TelegramForbiddenError = user blocked bot — skip silently
            failed += 1
            logger.debug(f"[SVC:Broadcast] Failed for user {user_id}: {type(e).__name__}")

        if i % 50 == 0:
            logger.info(f"[SVC:Broadcast] Progress {i}/{total}")

        await asyncio.sleep(0.05)  # Rate limit: 20 msg/s

    logger.info(f"[SVC:Broadcast] Done: sent={sent} failed={failed}")
    return {"sent": sent, "failed": failed, "total": total}
