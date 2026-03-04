import pytest


@pytest.mark.asyncio
async def test_security_headers_present(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("content-security-policy")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"


@pytest.mark.asyncio
async def test_cors_denied_when_origin_not_allowlisted(client):
    response = await client.get(
        "/api/health",
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 200
    # No allowlist configured in tests by default -> no ACAO header for foreign origins.
    assert "access-control-allow-origin" not in response.headers

