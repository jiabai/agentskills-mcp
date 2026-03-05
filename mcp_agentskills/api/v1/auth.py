from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.user import UserRepository
from mcp_agentskills.schemas.response import AccessTokenResponse, TokenPair
from mcp_agentskills.schemas.token import TokenRefresh
from mcp_agentskills.schemas.user import UserLoginCode, UserRegisterCode
from mcp_agentskills.schemas.verification import VerificationCodeRequest, VerificationCodeResponse
from mcp_agentskills.services.auth import AuthService
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


@router.post("/verification-code", response_model=VerificationCodeResponse)
async def send_verification_code(
    payload: VerificationCodeRequest,
    background_tasks: BackgroundTasks,
    session=Depends(get_async_session),
):
    service = get_verification_service(session)
    try:
        response = await service.send_code(payload.email, payload.purpose, schedule=background_tasks.add_task)
    except ValueError as exc:
        detail = str(exc)
        if detail == "RESEND_TOO_FREQUENT":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_verification_error_payload(detail) or detail,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_verification_error_payload(detail) or detail,
        ) from exc
    return response


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterCode, session=Depends(get_async_session)):
    verification_service = get_verification_service(session)
    service = AuthService(UserRepository(session))
    try:
        await verification_service.verify_code(payload.email, "register", payload.code)
        user = await service.register(
            email=payload.email,
            username=payload.username,
            password=None,
        )
    except ValueError as exc:
        detail = str(exc)
        if "already" in detail.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_verification_error_payload(detail) or detail,
        ) from exc
    token_pair = service.issue_token(user)
    return TokenPair(access_token=token_pair.access_token, refresh_token=token_pair.refresh_token)


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLoginCode, session=Depends(get_async_session)):
    verification_service = get_verification_service(session)
    service = AuthService(UserRepository(session))
    try:
        await verification_service.verify_code(payload.email, "login", payload.code)
        user = await service.user_repo.get_by_email(payload.email)
        if not user or not user.is_active:
            raise ValueError("Invalid credentials")
    except ValueError as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_verification_error_payload(detail) or detail,
        ) from exc
    token_pair = service.issue_token(user)
    return TokenPair(access_token=token_pair.access_token, refresh_token=token_pair.refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(payload: TokenRefresh, session=Depends(get_async_session)):
    service = AuthService(UserRepository(session))
    try:
        token_pair = await service.refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return AccessTokenResponse(access_token=token_pair.access_token)
