from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.rules.rule_engine import RuleEngine, RuleMatchResult
from app.persistence.models.rule import Rule
from app.persistence.repositories.rule_repo import RuleRepository
from app.persistence.repositories.rule_mapping_repo import RuleMappingRepository


class RuleService:
    """
    Service for rule lifecycle management and evaluation.

    Used by:
    - Admin mode (CRUD)
    - Runtime rule evaluation
    """

    def __init__(self):
        self.engine = RuleEngine()

    # ─────────────────────────────────────────────
    # Admin APIs
    # ─────────────────────────────────────────────

    async def create(
        self,
        *,
        session: AsyncSession,
        payload: Dict[str, Any],
    ) -> Rule:
        repo = RuleRepository(session)

        rule = await repo.create(
            rule_key=payload["rule_key"],
            version=payload.get("version", 1),
            category=payload["category"],
            conditions=payload["conditions"],
            effects=payload["effects"],
            is_active=True,
        )

        await session.commit()
        return rule

    async def list_all(
        self,
        *,
        session: AsyncSession,
    ) -> List[Rule]:
        repo = RuleRepository(session)
        return await repo.list_all()

    async def deactivate(
        self,
        *,
        session: AsyncSession,
        rule_id: UUID,
    ) -> None:
        repo = RuleRepository(session)
        await repo.deactivate(rule_id)
        await session.commit()

    # ─────────────────────────────────────────────
    # Runtime Evaluation
    # ─────────────────────────────────────────────

    async def evaluate_for_kundali(
        self,
        *,
        session: AsyncSession,
        kundali_core_id: UUID,
        kundali_chart,
    ) -> List[RuleMatchResult]:
        rule_repo = RuleRepository(session)
        mapping_repo = RuleMappingRepository(session)

        rules = await rule_repo.list_active()

        results = self.engine.evaluate(
            kundali=kundali_chart,
            rules=rules,
        )

        for result in results:
            for trigger in result.triggered_entities:
                await mapping_repo.create(
                    rule_id=result.rule.id,
                    kundali_core_id=kundali_core_id,
                    entity_type=trigger["entity_type"],
                    entity_key=trigger["entity_key"],
                    entity_snapshot=trigger["snapshot"],
                )

        await session.commit()
        return results
