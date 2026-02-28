"""
Broadcast service — send message to all non-banned users.
No Aiogram imports in function signatures except Bot type hint.
"""
import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repo import UserRepository


import json

async def send_to_all(text: str, bot, db: AsyncSession, redis_client=None) -> dict:
    """
    Send text message to all active users.
    Returns: {"sent": int, "failed": int, "total": int}
    """
    user_ids = await UserRepository.get_all_ids(db)
    total = len(user_ids)
    sent = 0
    failed = 0

    logger.info(f"[SVC:Broadcast] Starting broadcast to {total} users")

    if redis_client:
        await redis_client.set("broadcast:status", json.dumps({
            "status": "in_progress",
            "total": total,
            "sent": 0,
            "failed": 0
        }))

    for i, user_id in enumerate(user_ids, 1):
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            # TelegramForbiddenError = user blocked bot — skip silently
            failed += 1
            logger.debug(f"[SVC:Broadcast] Failed for user {user_id}: {type(e).__name__}")

        if i % 10 == 0:
            logger.info(f"[SVC:Broadcast] Progress {i}/{total}")
            if redis_client:
                await redis_client.set("broadcast:status", json.dumps({
                    "status": "in_progress",
                    "total": total,
                    "sent": sent,
                    "failed": failed
                }))

        await asyncio.sleep(0.05)  # Rate limit: 20 msg/s

    result = {"sent": sent, "failed": failed, "total": total}
    logger.info(f"[SVC:Broadcast] Done: sent={sent} failed={failed}")
    if redis_client:
        await redis_client.set("broadcast:status", json.dumps({
            "status": "completed",
            "total": total,
            "sent": sent,
            "failed": failed
        }))
        
    return result
