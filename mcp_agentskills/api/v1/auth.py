from fastapi import APIRouter, Depends, HTTPException, status

from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.schemas.response import TokenPair
from mcp_agentskills.schemas.token import TokenRefresh
from mcp_agentskills.schemas.user import UserCreate, UserLogin, UserResponse
from mcp_agentskills.services.auth import AuthService


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session=Depends(get_async_session)):
    service = AuthService(UserRepository(session))
    try:
        user = await service.register(
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
    except ValueError as exc:
        detail = str(exc)
        if "already" in detail.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, session=Depends(get_async_session)):
    service = AuthService(UserRepository(session))
    try:
        token_pair = await service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenPair(access_token=token_pair.access_token, refresh_token=token_pair.refresh_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: TokenRefresh, session=Depends(get_async_session)):
    service = AuthService(UserRepository(session))
    try:
        token_pair = await service.refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenPair(access_token=token_pair.access_token, refresh_token=token_pair.refresh_token)
