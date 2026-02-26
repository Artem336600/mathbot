"""
Session service — manages game sessions in Redis.
All Redis access goes through this service only.
No Aiogram imports.
"""
import json
from typing import Any

from loguru import logger
import redis.asyncio as aioredis

from bot.config import settings

_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


SESSION_TTL = 3600  # 1 hour


async def create_sprint_session(user_id: int, question_ids: list[int]) -> dict:
    """
    Sprint session format:
    {
        "questions": [id, ...],
        "current_idx": 0,
        "correct_count": 0,
        "total": N
    }
    """
    session = {
        "questions": question_ids,
        "current_idx": 0,
        "correct_count": 0,
        "total": len(question_ids),
    }
    key = f"sprint:{user_id}"
    await get_redis().setex(key, SESSION_TTL, json.dumps(session))
    logger.info(f"[SVC:Session] Created sprint session {user_id}: {len(question_ids)} questions")
    return session


async def create_training_session(user_id: int, topic_ids: list[int]) -> dict:
    """
    Training session format:
    {
        "topic_ids": [...],
        "difficulty": 1,
        "current_question_id": null,
        "solved_count": 0,
        "xp_earned": 0
    }
    """
    session = {
        "topic_ids": topic_ids,
        "difficulty": 1,
        "current_question_id": None,
        "solved_count": 0,
        "xp_earned": 0,
    }
    key = f"training:{user_id}"
    await get_redis().setex(key, SESSION_TTL, json.dumps(session))
    logger.info(f"[SVC:Session] Created training session {user_id}: topics={topic_ids}")
    return session


async def get_session(user_id: int, mode: str) -> dict | None:
    """mode: 'sprint' | 'training' | 'topics' | 'mistakes'"""
    key = f"{mode}:{user_id}"
    data = await get_redis().get(key)
    if data is None:
        logger.debug(f"[SVC:Session] No session found: mode={mode} user={user_id}")
        return None
    return json.loads(data)


async def update_session(user_id: int, mode: str, session: dict) -> None:
    key = f"{mode}:{user_id}"
    await get_redis().setex(key, SESSION_TTL, json.dumps(session))
    logger.debug(f"[SVC:Session] Updated session mode={mode} user={user_id}")


async def delete_session(user_id: int, mode: str) -> None:
    key = f"{mode}:{user_id}"
    await get_redis().delete(key)
    logger.debug(f"[SVC:Session] Deleted session mode={mode} user={user_id}")


async def set_temp(user_id: int, key_suffix: str, data: Any, ttl: int = SESSION_TTL) -> None:
    """Generic temp storage. key_suffix = e.g. 'topics_session', 'mistakes_session'"""
    key = f"{key_suffix}:{user_id}"
    await get_redis().setex(key, ttl, json.dumps(data))


async def get_temp(user_id: int, key_suffix: str) -> Any | None:
    key = f"{key_suffix}:{user_id}"
    data = await get_redis().get(key)
    return json.loads(data) if data else None


async def delete_temp(user_id: int, key_suffix: str) -> None:
    key = f"{key_suffix}:{user_id}"
    await get_redis().delete(key)
