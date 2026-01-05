from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.usage_repo import UsageRepository


class UsageService:
    """
    Read-only service for inspecting usage logs.

    Used by:
    - Admin mode
    """

    async def get_user_usage(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Dict[str, Any]:

        repo = UsageRepository(session)

        logs = await repo.list_for_user(
            user_id=user_id,
            start=start,
            end=end,
        )

        return {
            "user_id": str(user_id),
            "total_events": len(logs),
            "by_feature": self._aggregate_by_feature(logs),
            "logs": [
                {
                    "feature": log.feature,
                    "quantity": log.quantity,
                    "timestamp": log.created_at.isoformat(),
                }
                for log in logs
            ],
        }

    async def get_feature_usage(
        self,
        *,
        session: AsyncSession,
        feature: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Dict[str, Any]:

        repo = UsageRepository(session)

        logs = await repo.list_for_feature(
            feature=feature,
            start=start,
            end=end,
        )

        return {
            "feature": feature,
            "total_events": len(logs),
            "total_quantity": sum(log.quantity for log in logs),
            "logs": [
                {
                    "user_id": str(log.user_id),
                    "quantity": log.quantity,
                    "timestamp": log.created_at.isoformat(),
                }
                for log in logs
            ],
        }

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def _aggregate_by_feature(
        self,
        logs: List,
    ) -> Dict[str, int]:
        summary: Dict[str, int] = {}

        for log in logs:
            summary.setdefault(log.feature, 0)
            summary[log.feature] += log.quantity

        return summary
