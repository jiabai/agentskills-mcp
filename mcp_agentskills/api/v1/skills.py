from fastapi import APIRouter, Depends, HTTPException, status

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from mcp_agentskills.services.skill import SkillService


router = APIRouter()


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    skills = await service.list_skills(current_user)
    return [SkillResponse.model_validate(skill) for skill in skills]


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    try:
        skill = await service.create_skill(current_user, payload.name, payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    skill = await service.skill_repo.get_by_id(skill_id)
    if not skill or skill.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    payload: SkillUpdate,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    fields = payload.model_dump(exclude_unset=True)
    try:
        skill = await service.update_skill(current_user, skill_id, **fields)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    try:
        await service.delete_skill(current_user, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None
