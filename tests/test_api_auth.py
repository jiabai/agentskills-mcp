import httpx
import pytest

from mcp_agentskills.api_app import create_application
from mcp_agentskills.config.settings import settings


@pytest.mark.asyncio
async def test_register_login_refresh(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "api@example.com", "username": "apiuser", "password": "pass1234"},
    )
    assert register.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "api@example.com", "password": "pass1234"},
    )
    assert login.status_code == 200
    payload = login.json()
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert "token_type" not in payload
    refresh_token = payload["refresh_token"]
    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200


@pytest.mark.asyncio
async def test_refresh_requires_token(client):
    response = await client.post("/api/v1/auth/refresh", json={})
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
    assert isinstance(payload["detail"], str)
    assert "code" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_login_invalid_credentials_format(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bad@example.com", "username": "baduser", "password": "pass1234"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    payload = response.json()
    assert "detail" in payload
    assert "code" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_rate_limit_enforced():
    original_requests = settings.RATE_LIMIT_REQUESTS
    original_window = settings.RATE_LIMIT_WINDOW
    settings.RATE_LIMIT_REQUESTS = 1
    settings.RATE_LIMIT_WINDOW = 60
    app = create_application()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as session:
        first = await session.get("/health")
        second = await session.get("/health")
    settings.RATE_LIMIT_REQUESTS = original_requests
    settings.RATE_LIMIT_WINDOW = original_window
    assert first.status_code == 200
    assert second.status_code == 403


@pytest.mark.asyncio
async def test_health_returns_minimal_payload(client):
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"status": "healthy"}


@pytest.mark.asyncio
async def test_health_ignores_db_failure(monkeypatch):
    from mcp_agentskills import api_app

    class BrokenConnection:
        async def __aenter__(self):
            raise RuntimeError("db down")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class BrokenEngine:
        def connect(self):
            return BrokenConnection()

    monkeypatch.setattr(api_app, "engine", BrokenEngine())
    app = create_application()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as session:
        response = await session.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_unhandled_exception_uses_error_format(app, client):
    async def boom():
        raise RuntimeError("boom")

    app.add_api_route("/boom", boom, methods=["GET"])
    response = await client.get("/boom")
    assert response.status_code == 500
    payload = response.json()
    assert "detail" in payload
    assert "code" in payload
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_logging_middleware_records_request(client, monkeypatch):
    from mcp_agentskills.core.middleware import logging as logging_middleware

    captured = []

    def fake_info(message: str, *args, **kwargs):
        captured.append(message)

    monkeypatch.setattr(logging_middleware.logger, "info", fake_info)
    response = await client.get("/health")
    assert response.status_code == 200
    assert any("GET /health" in message for message in captured)


def test_loguru_writes_to_configured_file(tmp_path):
    original_log_file = settings.LOG_FILE
    original_log_level = settings.LOG_LEVEL
    original_log_format = settings.LOG_FORMAT
    settings.LOG_FILE = str(tmp_path / "app.log")
    settings.LOG_LEVEL = "INFO"
    settings.LOG_FORMAT = "json"
    try:
        create_application()
        from loguru import logger

        logger.info("log-test-message")
        content = (tmp_path / "app.log").read_text(encoding="utf-8")
        assert "log-test-message" in content
    finally:
        settings.LOG_FILE = original_log_file
        settings.LOG_LEVEL = original_log_level
        settings.LOG_FORMAT = original_log_format
