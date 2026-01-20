from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.usage_log import UsageLog


class UsageRepository(BaseRepository[UsageLog]):
    """
    Repository for UsageLog model.

    Tracks user actions for:
    - quota enforcement
    - billing
    - analytics
    """

    model = UsageLog

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(
        self,
        user_id,
        feature: str,
        quantity: int = 1
    ) -> UsageLog:
        """
        Create and persist a new usage log entry.
        """
        log = UsageLog(
            user_id=user_id,
            feature=feature,
            quantity=quantity
        )
        self.session.add(log)
        # We don't necessarily need to commit here if service layer handles it,
        # but BillingService.log_usage calls commit explicitly.
        # But 'add' in BaseRepository flushes.
        await self.session.flush()
        return log

    async def count_usage_for_user(
        self,
        user_id,
        feature: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> int:
        """
        Count usage events for a user within an optional time window.
        """
        stmt = select(func.count(UsageLog.id)).where(
            UsageLog.user_id == user_id
        )

        if feature:
            stmt = stmt.where(UsageLog.feature == feature)

        if since:
            stmt = stmt.where(UsageLog.created_at >= since)

        if until:
            stmt = stmt.where(UsageLog.created_at <= until)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_monthly_usage(
        self,
        user_id,
        feature: str | None = None
    ) -> int:
        """
        Count usage for the current calendar month.
        """
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return await self.count_usage_for_user(
            user_id=user_id,
            feature=feature,
            since=start_of_month,
            until=now
        )

    async def list_recent_usage(
        self,
        user_id,
        limit: int = 50
    ) -> list[UsageLog]:
        """
        Fetch recent usage events for a user.
        """
        stmt = (
            select(UsageLog)
            .where(UsageLog.user_id == user_id)
            .order_by(UsageLog.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
