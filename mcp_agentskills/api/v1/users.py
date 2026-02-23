from fastapi import APIRouter, Depends, HTTPException, status

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.core.security.password import verify_password
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.schemas.user import UserDelete, UserPasswordUpdate, UserResponse, UserUpdate
from mcp_agentskills.services.user import UserService


router = APIRouter()


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
