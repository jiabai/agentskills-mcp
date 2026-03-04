from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from mcp_agentskills.core.middleware.logging import _should_track_request
from mcp_agentskills.models.request_metric import RequestMetric
from mcp_agentskills.repositories.request_metric import RequestMetricRepository


def test_should_track_request_filters_auth_and_non_api():
    assert _should_track_request("/api/v1/auth/login") is False
    assert _should_track_request("/health") is False
    assert _should_track_request("/api/v1/skills") is True
    assert _should_track_request("/api/v1/dashboard/metrics/cleanup") is False


@pytest.mark.asyncio
async def test_cleanup_before_removes_old_metrics(async_session):
    repo = RequestMetricRepository(async_session)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    old_bucket = now - timedelta(days=10)
    new_bucket = now - timedelta(days=1)
    async_session.add_all(
        [
            RequestMetric(
                user_id="user",
                bucket_start=old_bucket,
                total_count=1,
                success_count=1,
                failure_count=0,
            ),
            RequestMetric(
                user_id="user",
                bucket_start=new_bucket,
                total_count=2,
                success_count=2,
                failure_count=0,
            ),
        ]
    )
    await async_session.commit()

    await repo.cleanup_before(now - timedelta(days=5))

    result = await async_session.execute(
        select(func.count()).select_from(RequestMetric).where(RequestMetric.user_id == "user")
    )
    assert int(result.scalar_one()) == 1
