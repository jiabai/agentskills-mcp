from fastapi import APIRouter

from mcp_agentskills.api.v1.auth import router as auth_router
from mcp_agentskills.api.v1.skills import router as skills_router
from mcp_agentskills.api.v1.tokens import router as tokens_router
from mcp_agentskills.api.v1.users import router as users_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(tokens_router, prefix="/tokens", tags=["tokens"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
