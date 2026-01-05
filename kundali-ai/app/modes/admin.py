from fastapi import APIRouter, Depends, HTTPException, status

from app.services.kundali_service import KundaliService
from app.services.rule_service import RuleService
from app.services.usage_service import UsageService
from app.api.dependencies import get_admin_user


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)],
)


# ─────────────────────────────────────────────
# Kundali Debug / Recompute
# ─────────────────────────────────────────────

@router.post("/kundali/recompute")
async def recompute_kundali(
    birth_profile_id: str,
    kundali_service: KundaliService = Depends(),
):
    """
    Force recomputation of kundali (admin only).
    """
    return await kundali_service.recompute(birth_profile_id)


# ─────────────────────────────────────────────
# Rule Management
# ─────────────────────────────────────────────

@router.post("/rules")
async def create_rule(
    rule_payload: dict,
    rule_service: RuleService = Depends(),
):
    """
    Create a new astrology rule.
    """
    return await rule_service.create(rule_payload)


@router.get("/rules")
async def list_rules(
    rule_service: RuleService = Depends(),
):
    """
    List all rules (including inactive).
    """
    return await rule_service.list_all()


@router.post("/rules/{rule_id}/deactivate")
async def deactivate_rule(
    rule_id: str,
    rule_service: RuleService = Depends(),
):
    """
    Deactivate a rule safely.
    """
    await rule_service.deactivate(rule_id)
    return {"status": "deactivated"}


# ─────────────────────────────────────────────
# Usage & Audit
# ─────────────────────────────────────────────

@router.get("/usage/{user_id}")
async def get_user_usage(
    user_id: str,
    usage_service: UsageService = Depends(),
):
    """
    Inspect usage logs for a user.
    """
    return await usage_service.get_user_usage(user_id)
