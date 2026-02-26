from typing import Any, List, cast

from pydantic import ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DEBUG: bool = False
    CORS_ORIGINS: List[str] = []

    TIMEZONE: str = "UTC"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/var/log/agentskills/app.log"

    SKILL_STORAGE_PATH: str = "/data/skills"

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    FLOW_LLM_API_KEY: str = ""
    FLOW_LLM_BASE_URL: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    import json

                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_cors_origins(self):
        if not self.DEBUG and (not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS):
            raise ValueError("生产环境 CORS_ORIGINS 必须显式配置且不能包含通配符 '*'")
        return self

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY 长度必须至少 32 字符")
        return v

    @field_validator("DATABASE_POOL_SIZE", "DATABASE_MAX_OVERFLOW")
    @classmethod
    def validate_pool_settings(cls, v, info: ValidationInfo):
        field_name = info.field_name
        if v < 1:
            raise ValueError(f"{field_name} 必须至少为 1")
        if v > 100:
            raise ValueError(f"{field_name} 不能超过 100")
        return v

    @field_validator("DATABASE_POOL_TIMEOUT", "DATABASE_POOL_RECYCLE")
    @classmethod
    def validate_timeout_settings(cls, v, info: ValidationInfo):
        field_name = info.field_name
        if v < 1:
            raise ValueError(f"{field_name} 必须至少为 1 秒")
        if v > 3600:
            raise ValueError(f"{field_name} 不能超过 3600 秒")
        return v

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = cast(Any, Settings)()
