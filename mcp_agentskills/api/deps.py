from fastapi import Depends

from mcp_agentskills.core.middleware.auth import get_current_active_user
from mcp_agentskills.db.session import get_async_session


async def get_db_session():
    async for session in get_async_session():
        yield session


CurrentUser = Depends(get_current_active_user)
