from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.rule import Rule


class RuleRepository(BaseRepository[Rule]):
    """
    Repository for astrology rules.

    Handles persistence only.
    Evaluation happens in the rule engine.
    """

    model = Rule

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_active(self) -> list[Rule]:
        """
        Fetch all active rules.
        """
        stmt = select(Rule).where(Rule.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_category(self, category: str) -> list[Rule]:
        """
        Fetch rules by category (career, marriage, health, etc.).
        """
        stmt = select(Rule).where(
            Rule.category == category,
            Rule.is_active.is_(True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_version(self, rule_key: str) -> Rule | None:
        """
        Fetch the latest version of a rule by its key.
        """
        stmt = (
            select(Rule)
            .where(Rule.rule_key == rule_key)
            .order_by(Rule.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def deactivate_rule(self, rule_id) -> None:
        """
        Soft-deactivate a rule (admin use).
        """
        rule = await self.get_by_id(rule_id)
        if rule:
            rule.is_active = False
            await self.session.flush()
