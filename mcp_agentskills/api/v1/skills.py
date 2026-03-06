from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.skill_version import SkillVersionRepository
from mcp_agentskills.schemas.skill_download import SkillDownloadRequest, SkillDownloadResponse
from mcp_agentskills.schemas.skill_lifecycle import SkillInstallInstructionsResponse, SkillVersionDiffResponse
from mcp_agentskills.schemas.skill import SkillCreate, SkillListResponse, SkillResponse, SkillUpdate
from mcp_agentskills.schemas.skill_version import SkillVersionListResponse, SkillVersionResponse
from mcp_agentskills.services.skill import SkillService


router = APIRouter()


@router.get("", response_model=SkillListResponse)
@router.get("/", response_model=SkillListResponse)
async def list_skills(
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    include_inactive: bool = False,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    skills = await service.list_skills(
        current_user,
        skip=skip,
        limit=limit,
        query=q,
        include_inactive=include_inactive,
    )
    total = await service.skill_repo.count_by_user(
        current_user.id,
        query=q,
        include_inactive=include_inactive,
    )
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
        skill = await service.create_skill(current_user, payload.name, payload.description, payload.tags)
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
    metadata: str | None = Form(None),
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    content = await file.read()
    try:
        filename = file.filename or ""
        if filename.lower().endswith(".zip"):
            payload = await service.upload_zip(current_user, skill_id, filename, content, metadata)
            return payload
        filename = await service.upload_file(current_user, skill_id, filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"filename": filename}


@router.post("/download", response_model=SkillDownloadResponse)
async def download_skill(
    payload: SkillDownloadRequest,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        result = await service.download_skill(current_user, payload.skill_id, payload.version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SkillDownloadResponse.model_validate(result)


@router.post("/{skill_id}/deactivate", response_model=SkillResponse)
async def deactivate_skill(
    skill_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        skill = await service.deactivate_skill(current_user, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return skill


@router.post("/{skill_id}/activate", response_model=SkillResponse)
async def activate_skill(
    skill_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        skill = await service.activate_skill(current_user, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return skill


@router.get("/{skill_id}/versions", response_model=SkillVersionListResponse)
async def list_skill_versions(
    skill_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        versions = await service.list_versions(current_user, skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SkillVersionListResponse(items=[SkillVersionResponse.model_validate(item) for item in versions])


@router.get("/{skill_id}/versions/{version}/install-instructions", response_model=SkillInstallInstructionsResponse)
async def get_install_instructions(
    skill_id: str,
    version: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        payload = await service.get_install_instructions(current_user, skill_id, version)
    except ValueError as exc:
        if str(exc) == "SKILL_DEACTIVATED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={"detail": "Skill deactivated", "code": "SKILL_DEACTIVATED"},
            ) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SkillInstallInstructionsResponse.model_validate(payload)


@router.get("/{skill_id}/versions/diff", response_model=SkillVersionDiffResponse)
async def diff_skill_versions(
    skill_id: str,
    from_version: str = Query(..., alias="from"),
    to_version: str = Query(..., alias="to"),
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        payload = await service.diff_versions(current_user, skill_id, from_version, to_version)
    except ValueError as exc:
        if str(exc) == "SKILL_DEACTIVATED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={"detail": "Skill deactivated", "code": "SKILL_DEACTIVATED"},
            ) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SkillVersionDiffResponse.model_validate(payload)


@router.post("/{skill_id}/versions/{version}/rollback", response_model=SkillVersionResponse)
async def rollback_skill_version(
    skill_id: str,
    version: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        record = await service.rollback_version(current_user, skill_id, version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SkillVersionResponse.model_validate(record)


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
        if str(exc) == "SKILL_DEACTIVATED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={"detail": "Skill deactivated", "code": "SKILL_DEACTIVATED"},
            ) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return files


@router.get("/{skill_id}/files/{file_path:path}")
async def read_skill_file(
    skill_id: str,
    file_path: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = SkillService(SkillRepository(session), SkillVersionRepository(session))
    try:
        content = await service.read_skill_file(current_user, skill_id, file_path)
    except ValueError as exc:
        if str(exc) == "SKILL_DEACTIVATED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={"detail": "Skill deactivated", "code": "SKILL_DEACTIVATED"},
            ) from exc
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(content, media_type="text/plain; charset=utf-8")
