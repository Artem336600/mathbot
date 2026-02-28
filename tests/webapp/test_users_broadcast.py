import pytest
from httpx import AsyncClient
import json

@pytest.mark.asyncio
async def test_get_users_empty(authed_client: AsyncClient):
    resp = await authed_client.get("/api/users/")
    assert resp.status_code == 200
    # There is 1 user: the admin himself (id 12345)
    users = resp.json()
    assert len(users) == 1
    assert users[0]["id"] == 12345

@pytest.mark.asyncio
async def test_get_users_with_data(authed_client: AsyncClient, db_session):
    from db.models import User
    u = User(id=1, first_name="Test", is_banned=False)
    db_session.add(u)
    await db_session.commit()

    resp = await authed_client.get("/api/users/")
    assert resp.status_code == 200
    data = resp.json()
    # 2 users: admin (12345) + Test (1)
    assert len(data) == 2
    assert data[0]["first_name"] == "Test"

@pytest.mark.asyncio
async def test_ban_user(authed_client: AsyncClient, db_session):
    from db.models import User
    u = User(id=2, first_name="BanMe", is_banned=False)
    db_session.add(u)
    await db_session.commit()

    ban_resp = await authed_client.post("/api/users/2/ban")
    assert ban_resp.status_code == 200

    check_resp = await authed_client.get("/api/users/")
    user = next((x for x in check_resp.json() if x["id"] == 2), None)
    assert user is not None
    assert user["is_banned"] is True

@pytest.mark.asyncio
async def test_broadcast_preview(authed_client: AsyncClient):
    payload = {"text": "<b>Hello</b>"}
    resp = await authed_client.post("/api/broadcast/preview", json=payload)
    assert resp.status_code == 200
    assert resp.json()["html"] == "<b>Hello</b>"

@pytest.mark.asyncio
async def test_broadcast_status(authed_client: AsyncClient, mocker):
    from webapp.routers.broadcast import get_redis
    from webapp.main import app
    from unittest.mock import AsyncMock

    mock_redis = AsyncMock()
    # mock get return value
    mock_redis.get.return_value = json.dumps({"status": "in_progress", "sent": 10, "failed": 2, "total": 100})

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_redis] = override_get_redis

    resp = await authed_client.get("/api/broadcast/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["sent"] == 10
    assert data["failed"] == 2
    assert data["total"] == 100

    app.dependency_overrides.pop(get_redis, None)
