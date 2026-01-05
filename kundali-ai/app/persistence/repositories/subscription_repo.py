from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.subscription import Subscription


class SubscriptionRepository(BaseRepository[Subscription]):
    """
    Repository for Subscription model.

    Handles persistence for plans, status, and validity.
    """

    model = Subscription

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_active_for_user(
        self,
        user_id
    ) -> Subscription | None:
        """
        Fetch the currently active subscription for a user.
        """
        now = datetime.utcnow()

        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
            Subscription.start_date <= now,
            Subscription.end_date >= now,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id
    ) -> list[Subscription]:
        """
        Fetch all subscriptions for a user (history).
        """
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.start_date.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def deactivate_subscription(
        self,
        subscription_id
    ) -> None:
        """
        Soft-deactivate a subscription.
        """
        subscription = await self.get_by_id(subscription_id)
        if subscription:
            subscription.is_active = False
            await self.session.flush()
