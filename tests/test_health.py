import pytest


@pytest.mark.asyncio
async def test_health_reports_component_status(client):
    """/health har bir komponent holatini qaytarishi kerak (Redis testda bo'lmasa 503 - bu ham to'g'ri javob)."""
    response = await client.get("/health")
    assert response.status_code in (200, 503)
    body = response.json()
    assert set(body["checks"]) == {"database", "redis"}
    assert (response.status_code == 200) == (body["status"] == "ok")
