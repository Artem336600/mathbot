from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from loguru import logger

from bot.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set True for SQL query logs
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

logger.debug(f"[DB] Engine created for: {settings.database_url[:40]}...")

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency: yields a DB session and closes it after use."""
    async with async_session_factory() as session:
        yield session
