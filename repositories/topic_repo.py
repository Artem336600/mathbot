"""Topic repository — CRUD only."""
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Topic


class TopicRepository:
    @staticmethod
    async def get_all(db: AsyncSession) -> list[Topic]:
        result = await db.execute(
            select(Topic).where(Topic.is_active == True).order_by(Topic.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(topic_id: int, db: AsyncSession) -> Topic | None:
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(title: str, theory_text: str, db: AsyncSession, image_url: str | None = None) -> Topic:
        logger.debug(f"[REPO:Topic] create title={title!r} has_image={bool(image_url)}")
        topic = Topic(title=title, theory_text=theory_text, image_url=image_url)
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        return topic

    @staticmethod
    async def update(topic_id: int, db: AsyncSession, **kwargs) -> Topic | None:
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        topic = result.scalar_one_or_none()
        if topic:
            for key, value in kwargs.items():
                setattr(topic, key, value)
            await db.commit()
            await db.refresh(topic)
        return topic

    @staticmethod
    async def delete(topic_id: int, db: AsyncSession) -> bool:
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        topic = result.scalar_one_or_none()
        if topic:
            await db.delete(topic)
            await db.commit()
            logger.info(f"[REPO:Topic] deleted topic_id={topic_id}")
            return True
        return False
