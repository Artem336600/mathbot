import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from hypothesis import settings, Verbosity, HealthCheck, Phase

# Hypothesis profiles
settings.register_profile("ci", max_examples=1000, deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=50, deadline=None)
settings.load_profile("dev")  # default to dev

from db.models import Base

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="function")
async def db_engine():
    """Create a new database engine and tables for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db(db_engine) -> AsyncSession:
    """Provide a new session for each test."""
    async with test_session_factory() as session:
        yield session

@pytest.fixture(scope="function")
def mock_redis(mocker):
    """Mock Redis session service calls."""
    mock_redis_client = AsyncMock()
    mocker.patch("services.session_service.get_redis", return_value=mock_redis_client)
    return mock_redis_client
