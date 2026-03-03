from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.core.middleware.logging import get_success_rate
from mcp_agentskills.db.session import get_async_session
from mcp_agentskills.repositories.skill import SkillRepository
from mcp_agentskills.repositories.token import TokenRepository
from mcp_agentskills.schemas.response import DashboardOverviewResponse


router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    current_user=Depends(get_current_active_user),
    session=Depends(get_async_session),
):
    skill_repo = SkillRepository(session)
    token_repo = TokenRepository(session)
    active_skills = await skill_repo.count_active_by_user(current_user.id)
    available_tokens = await token_repo.count_available_by_user(current_user.id, datetime.now(timezone.utc))
    success_rate, total = await get_success_rate(str(current_user.id))
    return DashboardOverviewResponse(
        active_skills=active_skills,
        available_tokens=available_tokens,
        success_rate=success_rate,
        success_rate_window_hours=24,
        success_rate_total=total,
    )
