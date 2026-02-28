import pytest
import hmac
import hashlib
from urllib.parse import urlencode

from webapp.auth import validate_init_data
from bot.config import settings

def test_validate_init_data_invalid():
    assert validate_init_data("invalid_string", "test_token") is None

def test_validate_init_data_valid():
    bot_token = settings.bot_token
    
    # 1. Create a fake payload
    user_json = '{"id":123,"first_name":"Test Admin"}'
    data = {"user": user_json, "auth_date": "1710000000", "query_id": "AA..."}
    
    # 2. Sort keys alphabetically
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    
    # 3. Compute hash
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # 4. Add hash to data and build query string
    data["hash"] = calculated_hash
    init_data = urlencode(data)
    
    # 5. Validate
    result = validate_init_data(init_data, bot_token)
    
    assert result is not None
    assert result["id"] == 123
    assert result["first_name"] == "Test Admin"

@pytest.mark.asyncio
async def test_auth_middleware_no_header(client):
    response = await client.get("/api/stats/")
    assert response.status_code == 401
    assert "X-Init-Data" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_middleware_invalid_signature(client):
    client.headers = {"X-Init-Data": "query_id=123&hash=invalid"}
    response = await client.get("/api/stats/")
    assert response.status_code == 401
    assert "signature" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_middleware_not_admin(client, monkeypatch):
    from bot.config import settings
    # Empty admin_ids
    monkeypatch.setattr(settings, "admin_ids", [999999])
    
    # test_dev=123 bypasses initData signature but then checks admin rights
    client.headers = {"X-Init-Data": "test_dev=123"}
    response = await client.get("/api/stats/")
    
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_middleware_banned_admin(client, db_session, monkeypatch):
    from bot.config import settings
    from tests.factories import create_user
    
    # 1. Setup admin who is banned
    uid = 55555
    monkeypatch.setattr(settings, "admin_ids", [uid])
    
    # We must create this user in DB because auth check now hits DB
    user = create_user(id=uid, is_admin=True, is_banned=True)
    db_session.add(user)
    await db_session.commit()
    
    # 2. Try to access
    client.headers = {"X-Init-Data": f"test_dev={uid}"}
    response = await client.get("/api/stats/")
    
    assert response.status_code == 403
    assert "banned" in response.json()["detail"]
