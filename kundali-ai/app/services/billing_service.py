from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.subscription_repo import SubscriptionRepository
from app.persistence.repositories.usage_repo import UsageRepository


class QuotaExceededError(Exception):
    """Raised when a user exceeds quota for a feature."""


class BillingService:
    """
    Handles quota enforcement and usage logging.
    """

    PLAN_QUOTAS = {
        "free": {
            "kundali": 1,
            "ask_llm": 5,
            "pdf_report": 1,
            "voice": 2,
        },
        "pro": {
            "kundali": 10,
            "ask_llm": 100,
            "pdf_report": 20,
            "voice": 20,
        },
        "enterprise": {
            "kundali": 10_000,
            "ask_llm": 100_000,
            "pdf_report": 10_000,
            "voice": 10_000,
        },
    }

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def assert_quota(
        self,
        session: AsyncSession,
        user_id: UUID,
        feature: str,
        quantity: int = 1,
    ) -> None:
        used = await self._get_usage(session, user_id, feature)
        limit = await self._get_quota_limit(session, user_id, feature)

        if used + quantity > limit:
            raise QuotaExceededError(
                f"Quota exceeded for feature '{feature}' "
                f"(used={used}, limit={limit})"
            )

    async def log_usage(
        self,
        session: AsyncSession,
        user_id: UUID,
        feature: str,
        quantity: int = 1,
    ) -> None:
        repo = UsageRepository(session)
        await repo.create(
            user_id=user_id,
            feature=feature,
            quantity=quantity,
        )
        await session.commit()

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    async def _get_quota_limit(
        self,
        session: AsyncSession,
        user_id: UUID,
        feature: str,
    ) -> int:
        repo = SubscriptionRepository(session)
        sub = await repo.get_active_for_user(user_id)
        plan = sub.plan if sub else "free"
        return self.PLAN_QUOTAS.get(plan, {}).get(feature, 0)

    async def _get_usage(
        self,
        session: AsyncSession,
        user_id: UUID,
        feature: str,
    ) -> int:
        repo = UsageRepository(session)
        return await repo.count_monthly_usage(
            user_id=user_id,
            feature=feature,
        )
