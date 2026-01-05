from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.kundali_service import KundaliService
from app.api.dependencies import get_current_user
from app.persistence.db import get_db_session


router = APIRouter()


# ─────────────────────────────────────────────
# Request Schema
# ─────────────────────────────────────────────

class KundaliCreateRequest(BaseModel):
    name: str = Field(..., example="Tanishq")
    birth_date: str = Field(..., example="1998-12-04")
    birth_time: str = Field(..., example="16:03")
    birth_place: str = Field(..., example="Pune, Maharashtra, India")  # ✅
    latitude: float = Field(..., example=18.9777)
    longitude: float = Field(..., example=76.4953)
    timezone: str = Field(..., example="Asia/Kolkata")


# ─────────────────────────────────────────────
# Response Schema (loose by design)
# ─────────────────────────────────────────────

class KundaliCreateResponse(BaseModel):
    birth_profile_id: UUID
    kundali_core_id: UUID
    kundali: Dict[str, Any]
    derived: Dict[str, Any]
    divisional: Dict[str, Any]


# ─────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────

@router.post(
    "/kundali",
    response_model=KundaliCreateResponse,
    summary="Create kundali from birth details",
)
async def create_kundali(
    payload: KundaliCreateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a kundali for the authenticated user.
    """

    service = KundaliService()

    result = await service.create_kundali(
        session=session,
        user_id=user.id,
        payload=payload.model_dump(),
    )

    return result
