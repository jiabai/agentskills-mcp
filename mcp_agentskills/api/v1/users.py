from fastapi import APIRouter, Depends, HTTPException, Request, status

from mcp_agentskills.config.settings import settings
from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.core.security.password import verify_password
from mcp_agentskills.core.security.rbac import has_permission
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.audit_log import AuditLogRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.schemas.auth import UserIdentityUpdate
from mcp_agentskills.schemas.user import UserBindEmail, UserDelete, UserPasswordUpdate, UserResponse, UserUpdate
from mcp_agentskills.services.audit import AuditService
from mcp_agentskills.services.user import UserService
from mcp_agentskills.services.verification_code import get_verification_service


router = APIRouter()

_verification_error_messages = {
    "CODE_EXPIRED": "验证码已过期",
    "CODE_INVALID": "验证码错误",
    "TOO_MANY_ATTEMPTS": "尝试次数过多，请稍后再试",
    "RESEND_TOO_FREQUENT": "重发过于频繁",
}


def _verification_error_payload(detail: str) -> dict | None:
    message = _verification_error_messages.get(detail)
    if not message:
        return None
    return {"detail": message, "code": detail}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = UserService(UserRepository(session))
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return current_user
    updated = await service.update_user(current_user, **fields)
    return updated


@router.put("/me/password", response_model=UserResponse)
async def change_password(
    payload: UserPasswordUpdate,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password")
    service = UserService(UserRepository(session))
    updated = await service.change_password(current_user, payload.new_password)
    return updated


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    payload: UserDelete,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = UserService(UserRepository(session))
    try:
        await service.delete_user(current_user, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return None


@router.post("/bind-email")
async def bind_email(
    payload: UserBindEmail,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    verification_service = get_verification_service(session)
    try:
        await verification_service.verify_code(payload.email, "bind_email", payload.code)
    except ValueError as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_verification_error_payload(detail) or detail,
        ) from exc
    user_repo = UserRepository(session)
    existing = await user_repo.get_by_email(payload.email)
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    service = UserService(user_repo)
    await service.update_user(current_user, email=payload.email)
    return {"bound": True}


@router.put("/{user_id}/identity", response_model=UserResponse)
async def update_identity(
    request: Request,
    user_id: str,
    payload: UserIdentityUpdate,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    if not has_permission(current_user, "user.manage"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    user_repo = UserRepository(session)
    target = await user_repo.get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    fields = payload.model_dump(exclude_unset=True)
    service = UserService(user_repo)
    updated = await service.update_user(target, **fields)
    if settings.ENABLE_AUDIT_LOG:
        audit_service = AuditService(AuditLogRepository(session))
        await audit_service.create_event(
            actor_id=current_user.id,
            action="user.identity.update",
            target=target.id,
            ip=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            metadata=fields,
        )
    return updated
