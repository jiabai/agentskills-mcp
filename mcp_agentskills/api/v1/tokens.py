from fastapi import APIRouter, Depends, HTTPException, status

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.token import TokenRepository
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.schemas.token import TokenCreate, TokenResponse
from mcp_agentskills.services.token import TokenService


router = APIRouter()


@router.get("", response_model=list[TokenResponse])
async def list_tokens(
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = TokenService(TokenRepository(session), UserRepository(session))
    tokens = await service.list_tokens(current_user)
    return [TokenResponse.model_validate(token) for token in tokens]


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    payload: TokenCreate,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = TokenService(TokenRepository(session), UserRepository(session))
    token, value = await service.create_token_with_value(
        current_user,
        name=payload.name,
        expires_at=payload.expires_at,
    )
    response = TokenResponse.model_validate(token)
    response.token = value
    return response


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(
    token_id: str,
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    service = TokenService(TokenRepository(session), UserRepository(session))
    try:
        await service.revoke_token(current_user, token_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None
