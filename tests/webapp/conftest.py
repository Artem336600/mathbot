import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from db.models import Base
from webapp.main import app
from webapp.auth import get_db_session

# Test Database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session, mocker):
    from unittest.mock import AsyncMock
    from webapp.routers.broadcast import get_redis

    # Mock Redis
    mock_redis = AsyncMock()
    async def override_get_redis():
        yield mock_redis

    # Override FastAPI dependency for database session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        ac.mock_redis = mock_redis
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def mock_admin_init_data():
    # Helper to generate test init_data that bypasses the real auth
    # using the built-in dev backdoor we wrote in webapp/auth.py
    # NOTE: The dev backdoor requires the admin ID to be in settings.admin_ids
    # We can mock settings.admin_ids or better yet, inject a dependency override.
    pass

@pytest_asyncio.fixture
async def authed_client(client, db_session, monkeypatch):
    from bot.config import settings
    from tests.factories import create_user
    
    # 1. User 12345 will be our test admin
    uid = 12345
    monkeypatch.setattr(settings, "admin_ids", [uid])
    monkeypatch.setattr(settings, "webapp_auth_mode", "test_bypass")
    
    # 2. We MUST create this user in DB, as auth check now hits DB
    admin = create_user(id=uid, is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    
    client.headers = {"X-Init-Data": f"test_dev={uid}"}
    yield client
