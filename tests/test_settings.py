import importlib.util
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

settings_path = (
    Path(__file__).resolve().parents[1]
    / "mcp_agentskills"
    / "config"
    / "settings.py"
)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/agentskills"
)
os.environ.setdefault("SECRET_KEY", "a" * 32)
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("CORS_ORIGINS", "[\"http://localhost:3000\"]")
spec = importlib.util.spec_from_file_location("settings_module", settings_path)
assert spec is not None
assert spec.loader is not None
settings_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings_module)
Settings = settings_module.Settings


def base_settings_kwargs():
    return {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/agentskills",
        "SECRET_KEY": "a" * 32,
        "DEBUG": True,
        "CORS_ORIGINS": ["http://localhost:3000"],
        "FLOW_LLM_API_KEY": "key",
        "FLOW_LLM_BASE_URL": "https://api.example.com/v1",
    }


def test_parse_cors_origins_from_string():
    settings = Settings(
        **{
            **base_settings_kwargs(),
            "DEBUG": True,
            "CORS_ORIGINS": "http://a.com, http://b.com",
        }
    )
    assert settings.CORS_ORIGINS == ["http://a.com", "http://b.com"]


def test_secret_key_too_short():
    with pytest.raises(ValidationError):
        Settings(
            **{
                **base_settings_kwargs(),
                "SECRET_KEY": "short",
            }
        )


def test_pool_settings_minimum():
    with pytest.raises(ValidationError):
        Settings(
            **{
                **base_settings_kwargs(),
                "DATABASE_POOL_SIZE": 0,
            }
        )


def test_pool_settings_maximum():
    with pytest.raises(ValidationError):
        Settings(
            **{
                **base_settings_kwargs(),
                "DATABASE_MAX_OVERFLOW": 101,
            }
        )


def test_timeout_settings_minimum():
    with pytest.raises(ValidationError):
        Settings(
            **{
                **base_settings_kwargs(),
                "DATABASE_POOL_TIMEOUT": 0,
            }
        )


def test_timeout_settings_maximum():
    with pytest.raises(ValidationError):
        Settings(
            **{
                **base_settings_kwargs(),
                "DATABASE_POOL_RECYCLE": 3601,
            }
        )

