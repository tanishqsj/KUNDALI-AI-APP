from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.services.query_router import QueryRouter
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.persistence.db import get_db_session


router = APIRouter()


# ─────────────────────────────────────────────
# Request Schema
# ─────────────────────────────────────────────

class AskRequest(BaseModel):
    kundali_core_id: UUID = Field(..., description="Kundali core identifier")
    question: str = Field(..., example="What does my career look like this year?")


# ─────────────────────────────────────────────
# Response Schema
# ─────────────────────────────────────────────

class AskResponse(BaseModel):
    mode: str
    answer: Any
    explanations: Any | None = None
    transits: Any | None = None


# ─────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask an astrology question",
)
async def ask_question(
    payload: AskRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Ask a question about a kundali.
    """

    # ─────────────────────────────────────────────
    # Load kundali chart (read-only)
    # ─────────────────────────────────────────────

    repo = KundaliCoreRepository(session)
    kundali_core = await repo.get_by_id(payload.kundali_core_id)

    if not kundali_core:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kundali not found",
        )

    kundali_chart = kundali_core.to_domain()

    # ─────────────────────────────────────────────
    # Route question
    # ─────────────────────────────────────────────

    router_service = QueryRouter()

    result = await router_service.answer(
        session=session,
        user_id=user.id,
        kundali_core_id=payload.kundali_core_id,
        kundali_chart=kundali_chart,
        question=payload.question,
    )

    return result
