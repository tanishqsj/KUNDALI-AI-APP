from fastapi import APIRouter, Depends
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.db import get_db_session
from app.services.rule_service import RuleService
from app.services.explanation_service import ExplanationService


router = APIRouter()


@router.get(
    "/kundali/{kundali_core_id}",
    summary="Preview rule matches for a kundali",
)
async def preview_rules_for_kundali(
    kundali_core_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Preview rule matches and explanations for a kundali.
    """

    rule_service = RuleService()
    explanation_service = ExplanationService()

    rule_results = await rule_service.evaluate_for_kundali(
        session=session,
        kundali_core_id=kundali_core_id,
        kundali_chart=None,  # or load if needed
    )

    explanations = await explanation_service.build_explanations(
        session=session,
        kundali_core_id=kundali_core_id,
        rule_results=rule_results,
    )

    return {
        "matches": explanations,
    }
