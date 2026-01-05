from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rule_service import RuleService
from app.api.admin.schemas import RuleCreateRequest, RuleResponse
from app.api.dependencies import require_admin
from app.persistence.db import get_db_session


router = APIRouter()


@router.post(
    "",
    response_model=RuleResponse,
    summary="Create a new astrology rule",
)
async def create_rule(
    payload: RuleCreateRequest,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    service = RuleService()
    rule = await service.create(
        session=session,
        payload=payload.model_dump(),
    )
    return rule


@router.get(
    "",
    response_model=List[RuleResponse],
    summary="List all rules",
)
async def list_rules(
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    service = RuleService()
    return await service.list_all(session=session)


@router.post(
    "/{rule_id}/deactivate",
    summary="Deactivate a rule",
)
async def deactivate_rule(
    rule_id: UUID,
    admin=Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    service = RuleService()
    await service.deactivate(
        session=session,
        rule_id=rule_id,
    )
    return {"status": "deactivated"}
