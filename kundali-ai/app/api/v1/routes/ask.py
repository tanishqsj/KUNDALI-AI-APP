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
    # Route question
    # ─────────────────────────────────────────────

    # ─────────────────────────────────────────────
    # Route question (Streaming)
    # ─────────────────────────────────────────────

    router_service = QueryRouter()

    # We default to streaming for AI
    from fastapi.responses import StreamingResponse
    import json

    # For now, let's assume we want to stream ONLY if it's an AI-capable query.
    # But since we don't know yet if it's AI or Rules, we have a challenge.
    # However, since we are OPTIMIZING for perceived latency, let's switch to a full stream approach.
    # But wait, `stream_answer` in QueryRouter ONLY handles AI.
    # We should detect intent or just use the AI stream method if we are sure it's AI.
    # Given the app is "Ask AI", let's prioritize AI streaming.
    
    return StreamingResponse(
        router_service.stream_answer(
            session=session,
            user_id=user.id,
            kundali_core_id=payload.kundali_core_id,
            kundali_chart=kundali_chart,
            question=payload.question,
        ),
        media_type="text/event-stream"
    )
