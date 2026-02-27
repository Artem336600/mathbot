"""Question repository — CRUD and query methods only."""
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Question


class QuestionRepository:
    @staticmethod
    async def get_by_id(question_id: int, db: AsyncSession) -> Question | None:
        result = await db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_topic(topic_id: int, db: AsyncSession) -> list[Question]:
        result = await db.execute(
            select(Question)
            .where(Question.topic_id == topic_id)
            .order_by(Question.difficulty, Question.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_difficulty(
        topic_ids: list[int], difficulty: int, limit: int, db: AsyncSession
    ) -> list[Question]:
        result = await db.execute(
            select(Question)
            .where(Question.topic_id.in_(topic_ids))
            .where(Question.difficulty == difficulty)
            .order_by(func.random())
            .limit(limit)
        )
        questions = list(result.scalars().all())
        logger.debug(
            f"[REPO:Question] fetched {len(questions)} questions"
            f" difficulty={difficulty} topics={topic_ids}"
        )
        return questions

    @staticmethod
    async def get_random(
        topic_ids: list[int], limit: int, db: AsyncSession
    ) -> list[Question]:
        result = await db.execute(
            select(Question)
            .where(Question.topic_id.in_(topic_ids))
            .order_by(func.random())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        topic_id: int,
        text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: str,
        difficulty: int,
        explanation: str | None,
        db: AsyncSession,
        image_url: str | None = None,
    ) -> Question:
        q = Question(
            topic_id=topic_id,
            text=text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            difficulty=difficulty,
            explanation=explanation,
            image_url=image_url,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        logger.debug(f"[REPO:Question] created id={q.id} topic={topic_id}")
        return q

    @staticmethod
    async def update(question_id: int, db: AsyncSession, **kwargs) -> Question | None:
        result = await db.execute(select(Question).where(Question.id == question_id))
        q = result.scalar_one_or_none()
        if q:
            for key, value in kwargs.items():
                setattr(q, key, value)
            await db.commit()
            await db.refresh(q)
        return q
