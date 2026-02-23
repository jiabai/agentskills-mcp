import pytest


@pytest.mark.asyncio
async def test_mcp_http_requires_auth(client):
    response = await client.post("/mcp")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_sse_requires_auth(client):
    response = await client.get("/sse")
    assert response.status_code == 401
