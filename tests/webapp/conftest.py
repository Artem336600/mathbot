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
async def client(db_session):
    # Override FastAPI dependency for database session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
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
    
    # User 12345 will be our test admin
    monkeypatch.setattr(settings, "admin_ids", [12345])
    
    # We still need to create user 12345 in DB, because the dev backdoor
    # doesn't hit DB (wait, let's see auth.py: dev stub creates mock User object immediately)
    # Actually dev stub returns User object immediately bypassing DB entirely!
    client.headers = {"X-Init-Data": "test_dev=12345"}
    yield client
