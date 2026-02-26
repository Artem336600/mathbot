"""UserProgress repository — history of answered questions."""
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserProgress


class ProgressRepository:
    @staticmethod
    async def add(user_id: int, question_id: int, is_correct: bool, db: AsyncSession) -> UserProgress:
        entry = UserProgress(user_id=user_id, question_id=question_id, is_correct=is_correct)
        db.add(entry)
        await db.commit()
        logger.debug(f"[REPO:Progress] user={user_id} q={question_id} correct={is_correct}")
        return entry

    @staticmethod
    async def get_accuracy(user_id: int, db: AsyncSession) -> float:
        """Returns accuracy as float 0.0–1.0."""
        total_result = await db.execute(
            select(func.count()).where(UserProgress.user_id == user_id)
        )
        total = total_result.scalar() or 0
        if total == 0:
            return 0.0

        correct_result = await db.execute(
            select(func.count()).where(
                UserProgress.user_id == user_id, UserProgress.is_correct == True
            )
        )
        correct = correct_result.scalar() or 0
        return round(correct / total, 4)

    @staticmethod
    async def get_total_count(user_id: int, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count()).where(UserProgress.user_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_solved_ids(user_id: int, topic_id: int, db: AsyncSession) -> list[int]:
        """Returns set of question_ids solved correctly by user in given topic."""
        from db.models import Question
        result = await db.execute(
            select(UserProgress.question_id)
            .join(Question, UserProgress.question_id == Question.id)
            .where(
                UserProgress.user_id == user_id,
                UserProgress.is_correct == True,
                Question.topic_id == topic_id,
            )
            .distinct()
        )
        return list(result.scalars().all())
