from datetime import datetime

from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class SkillUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    skill_dir: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    items: list[SkillResponse]
    total: int
