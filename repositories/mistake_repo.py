"""UserMistake repository — CRUD only."""
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Question, UserMistake


class MistakeRepository:
    @staticmethod
    async def add(user_id: int, question_id: int, db: AsyncSession) -> UserMistake | None:
        """Add mistake only if not already present and not fixed."""
        existing = await db.execute(
            select(UserMistake).where(
                UserMistake.user_id == user_id,
                UserMistake.question_id == question_id,
                UserMistake.is_fixed == False,
            )
        )
        if existing.scalar_one_or_none():
            logger.debug(f"[REPO:Mistake] Already exists user={user_id} q={question_id}")
            return None
        mistake = UserMistake(user_id=user_id, question_id=question_id)
        db.add(mistake)
        await db.commit()
        await db.refresh(mistake)
        logger.debug(f"[REPO:Mistake] Added mistake id={mistake.id} user={user_id} q={question_id}")
        return mistake

    @staticmethod
    async def get_all(user_id: int, db: AsyncSession) -> list[UserMistake]:
        result = await db.execute(
            select(UserMistake)
            .where(UserMistake.user_id == user_id, UserMistake.is_fixed == False)
            .order_by(UserMistake.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_topic(
        user_id: int, topic_id: int, db: AsyncSession
    ) -> list[UserMistake]:
        result = await db.execute(
            select(UserMistake)
            .join(Question, UserMistake.question_id == Question.id)
            .where(
                UserMistake.user_id == user_id,
                UserMistake.is_fixed == False,
                Question.topic_id == topic_id,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_fixed(mistake_id: int, db: AsyncSession) -> bool:
        result = await db.execute(select(UserMistake).where(UserMistake.id == mistake_id))
        mistake = result.scalar_one_or_none()
        if mistake:
            mistake.is_fixed = True
            await db.commit()
            logger.debug(f"[REPO:Mistake] Fixed mistake_id={mistake_id}")
            return True
        return False

    @staticmethod
    async def count(user_id: int, db: AsyncSession) -> int:
        result = await db.execute(
            select(UserMistake).where(
                UserMistake.user_id == user_id, UserMistake.is_fixed == False
            )
        )
        return len(result.scalars().all())

    @staticmethod
    async def get_topics_with_mistakes(user_id: int, db: AsyncSession) -> list[int]:
        """Returns list of topic_ids that have unfixed mistakes."""
        result = await db.execute(
            select(Question.topic_id)
            .join(UserMistake, UserMistake.question_id == Question.id)
            .where(
                UserMistake.user_id == user_id, UserMistake.is_fixed == False
            )
            .distinct()
        )
        return list(result.scalars().all())
