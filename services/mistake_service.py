"""Mistake service — business logic for mistake workflow."""
import random

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserMistake
from repositories.mistake_repo import MistakeRepository
from repositories.question_repo import QuestionRepository


async def add_mistake(user_id: int, question_id: int, db: AsyncSession) -> None:
    """Add mistake (deduplication handled in repo)."""
    await MistakeRepository.add(user_id, question_id, db)
    logger.debug(f"[SVC:Mistake] add_mistake user={user_id} q={question_id}")


async def get_mistakes(
    user_id: int, topic_id: int | None, db: AsyncSession
) -> list[UserMistake]:
    if topic_id:
        return await MistakeRepository.get_by_topic(user_id, topic_id, db)
    return await MistakeRepository.get_all(user_id, db)


async def get_random_mistake(
    user_id: int, topic_id: int | None, db: AsyncSession
) -> UserMistake | None:
    """Get a random unfixed mistake, optionally filtered by topic."""
    mistakes = await get_mistakes(user_id, topic_id, db)
    if not mistakes:
        return None
    return random.choice(mistakes)


async def fix_mistake(mistake_id: int, user_id: int, db: AsyncSession) -> bool:
    """Mark mistake as fixed. Returns True if succeeded."""
    result = await MistakeRepository.mark_fixed(mistake_id, db)
    if result:
        logger.info(f"[SVC:Mistake] Mistake {mistake_id} fixed by user {user_id}")
    return result
