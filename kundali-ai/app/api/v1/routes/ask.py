from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Any, List

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
    match_id: UUID | None = Field(None, description="Optional match ID for compatibility questions")


# ─────────────────────────────────────────────
# Response Schema
# ─────────────────────────────────────────────

class AskResponse(BaseModel):
    mode: str
    answer: Any
    suggestions: List[str] | None = None
    explanations: Any | None = None
    transits: Any | None = None


# ─────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────

@router.post(
    "/ask",
    summary="Ask an astrology question (Streaming)",
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
    # Load Match Context (if match_id provided)
    # ─────────────────────────────────────────────
    
    match_context = None
    if payload.match_id:
        from app.persistence.repositories.kundali_match_repo import KundaliMatchRepository
        match_repo = KundaliMatchRepository(session)
        match_result = await match_repo.get_by_id(payload.match_id)
        
        if match_result:
            # Load boy's kundali
            boy_kundali = await repo.get_by_id(match_result.boy_kundali_id)
            # Load girl's kundali
            girl_kundali = await repo.get_by_id(match_result.girl_kundali_id)
            
            match_context = {
                "match_details": {
                    "boy_name": boy_kundali.birth_profile.name if boy_kundali and boy_kundali.birth_profile else "Boy",
                    "girl_name": girl_kundali.birth_profile.name if girl_kundali and girl_kundali.birth_profile else "Girl",
                    "total_score": match_result.total_score,
                    "max_score": match_result.max_score,
                    "percentage": ((match_result.total_score / match_result.max_score) * 100) if match_result.max_score else 0,
                    "compatibility_rating": match_result.verdict,
                    "factors": match_result.factors,
                },
                "boy_kundali": boy_kundali.to_domain() if boy_kundali else None,
                "girl_kundali": girl_kundali.to_domain() if girl_kundali else None,
            }

    # ─────────────────────────────────────────────
    # Route question (Streaming)
    # ─────────────────────────────────────────────

    router_service = QueryRouter()

    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        router_service.stream_answer(
            session=session,
            user_id=user.id,
            kundali_core_id=payload.kundali_core_id,
            kundali_chart=kundali_chart,
            question=payload.question,
            match_context=match_context,
        ),
        media_type="text/event-stream"
    )
