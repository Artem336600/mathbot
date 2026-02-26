"""User repository — CRUD operations only, no business logic."""
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


class UserRepository:
    @staticmethod
    async def get_or_create(
        tg_id: int, username: str | None, first_name: str, db: AsyncSession
    ) -> User:
        logger.debug(f"[REPO:User] get_or_create tg_id={tg_id}")
        result = await db.execute(select(User).where(User.id == tg_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(id=tg_id, username=username, first_name=first_name)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"[REPO:User] Created new user tg_id={tg_id}")
        else:
            # Update username/name if changed
            if user.username != username or user.first_name != first_name:
                user.username = username
                user.first_name = first_name
                await db.commit()
        return user

    @staticmethod
    async def get(tg_id: int, db: AsyncSession) -> User | None:
        result = await db.execute(select(User).where(User.id == tg_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(user: User, db: AsyncSession) -> User:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_all_ids(db: AsyncSession) -> list[int]:
        result = await db.execute(select(User.id).where(User.is_banned == False))
        return list(result.scalars().all())

    @staticmethod
    async def update_last_active(tg_id: int, db: AsyncSession) -> None:
        result = await db.execute(select(User).where(User.id == tg_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_active = datetime.now(timezone.utc)
            await db.commit()
