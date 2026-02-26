"""User service — registration and retrieval logic."""
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from repositories.user_repo import UserRepository


async def register_user(
    tg_id: int, username: str | None, first_name: str, db: AsyncSession
) -> User:
    """Get or create user. Called on /start."""
    user = await UserRepository.get_or_create(tg_id, username, first_name, db)
    logger.debug(f"[SVC:User] register_user tg_id={tg_id} level={user.level}")
    return user
