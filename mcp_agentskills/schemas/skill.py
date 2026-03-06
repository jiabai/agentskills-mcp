from datetime import datetime

from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=50)


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=50)


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
    skill_dir: str
    current_version: str | None
    is_active: bool
    cache_revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    items: list[SkillResponse]
    total: int
