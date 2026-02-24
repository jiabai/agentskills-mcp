from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.schemas.skill import SkillCreate, SkillListResponse, SkillResponse, SkillUpdate
from mcp_agentskills.services.skill import SkillService


router = APIRouter()


@router.get("", response_model=SkillListResponse)
@router.get("/", response_model=SkillListResponse)
async def list_skills(
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    skills = await service.list_skills(current_user, skip=skip, limit=limit, query=q)
    total = await service.skill_repo.count_by_user(current_user.id, query=q)
    return SkillListResponse(
        items=[SkillResponse.model_validate(skill) for skill in skills],
        total=total,
    )


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
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
    try:
        skill = await service.get_skill(current_user, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
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


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_skill_file(
    skill_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    content = await file.read()
    try:
        filename = await service.upload_file(current_user, skill_id, file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"filename": filename}


@router.get("/{skill_id}/files")
async def list_skill_files(
    skill_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session))
    try:
        files = await service.list_skill_files(current_user, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return files
