import pytest
import json
from unittest.mock import AsyncMock
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_broadcast_preview(authed_client: AsyncClient):
    payload = {"text": "<b>Hello</b>"}
    resp = await authed_client.post("/api/broadcast/preview", json=payload)
    assert resp.status_code == 200
    assert resp.json()["html"] == payload["text"]

@pytest.mark.asyncio
async def test_broadcast_send_success(authed_client: AsyncClient):
    # Mock redis to return no running broadcast
    authed_client.mock_redis.get.return_value = None
    
    payload = {"text": "Broadcast message"}
    resp = await authed_client.post("/api/broadcast/send", json=payload)
    
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"

@pytest.mark.asyncio
async def test_broadcast_send_already_running(authed_client: AsyncClient):
    # Mock redis to return a running broadcast status
    authed_client.mock_redis.get.return_value = json.dumps({"status": "in_progress"})
    
    payload = {"text": "Broadcast message"}
    resp = await authed_client.post("/api/broadcast/send", json=payload)
    
    assert resp.status_code == 400
    assert "already running" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_import_questions_validation_error(authed_client: AsyncClient, db_session):
    from tests.factories import create_topic
    
    topic = create_topic(id=20)
    db_session.add(topic)
    await db_session.commit()
    
    # Broken JSON structure (e.g. missing correct_option)
    invalid_data = [
        {"text": "Q1", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4"}
    ]
    files = {
        "file": ("questions.json", json.dumps(invalid_data), "application/json")
    }
    data = {"topic_id": 20}
    
    resp = await authed_client.post("/api/questions/import", data=data, files=files)
    
    assert resp.status_code == 200 # App handles validation and returns error keys in JSON
    res_json = resp.json()
    assert res_json["status"] == "error"
    assert "Row 1" in res_json["errors"][0]

@pytest.mark.asyncio
async def test_import_questions_success(authed_client: AsyncClient, db_session):
    from tests.factories import create_topic
    
    topic = create_topic(id=21)
    db_session.add(topic)
    await db_session.commit()
    
    valid_data = [
        {
            "text": "Correct Q", 
            "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4",
            "correct_option": "a", "difficulty": 1, "explanation": "Expl"
        }
    ]
    files = {
        "file": ("questions.json", json.dumps(valid_data), "application/json")
    }
    data = {"topic_id": 21}
    
    resp = await authed_client.post("/api/questions/import", data=data, files=files)
    
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["status"] == "success"
    assert res_json["imported"] == 1
