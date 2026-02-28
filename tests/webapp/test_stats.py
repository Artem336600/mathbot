import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_stats(authed_client: AsyncClient, db_session):
    resp = await authed_client.get("/api/stats/")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "total_questions" in data
    assert "total_answers" in data
    assert "answers_today" in data
