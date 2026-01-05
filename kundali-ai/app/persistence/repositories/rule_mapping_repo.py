from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.repositories.base import BaseRepository
from app.persistence.models.rule_mapping import RuleMapping


class RuleMappingRepository(BaseRepository[RuleMapping]):
    """
    Repository for RuleMapping model.

    Rule mappings link rules to kundali facts that caused them to match.
    Used for explainability, audits, and previews.
    """

    model = RuleMapping

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_kundali_core(
        self,
        kundali_core_id
    ) -> list[RuleMapping]:
        """
        Fetch all rule mappings for a given kundali core.
        """
        stmt = select(RuleMapping).where(
            RuleMapping.kundali_core_id == kundali_core_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_rule(
        self,
        rule_id
    ) -> list[RuleMapping]:
        """
        Fetch all mappings for a specific rule.
        """
        stmt = select(RuleMapping).where(
            RuleMapping.rule_id == rule_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_entity(
        self,
        entity_type: str,
        entity_key: str
    ) -> list[RuleMapping]:
        """
        Fetch mappings by entity type and key.

        Example:
        - entity_type = 'planet'
        - entity_key = 'Jupiter'
        """
        stmt = select(RuleMapping).where(
            RuleMapping.entity_type == entity_type,
            RuleMapping.entity_key == entity_key
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
