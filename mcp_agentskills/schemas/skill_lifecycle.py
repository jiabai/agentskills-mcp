from pydantic import BaseModel


class SkillInstallInstructionsResponse(BaseModel):
    strategy: str
    dependencies: list[str]
    requirements_text: str
    commands: list[str]


class SkillVersionDiffFile(BaseModel):
    path: str
    diff: str


class SkillVersionDiffResponse(BaseModel):
    from_version: str
    to_version: str
    added: list[str]
    removed: list[str]
    modified: list[SkillVersionDiffFile]
