import pytest


@pytest.mark.asyncio
async def test_token_lifecycle(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "tok@example.com", "username": "tokuser", "password": "pass1234"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "tok@example.com", "password": "pass1234"},
    )
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    created = await client.post("/api/v1/tokens", json={"name": "default"}, headers=headers)
    assert created.status_code == 201
    assert "token" in created.json()
    token_id = created.json()["id"]
    listed = await client.get("/api/v1/tokens", headers=headers)
    assert listed.status_code == 200
    payload = listed.json()
    assert "items" in payload
    assert payload["total"] == 1
    assert "token" not in payload["items"][0]
    revoked = await client.delete(f"/api/v1/tokens/{token_id}", headers=headers)
    assert revoked.status_code == 204
