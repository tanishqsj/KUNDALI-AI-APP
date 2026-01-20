from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
import base64
import os
import io
import re
import edge_tts
from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.persistence.db import get_db_session
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.services.query_router import QueryRouter
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("")
async def voice_interaction(
    kundali_core_id: UUID,
    audio: UploadFile = File(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Voice-in, Voice-out streaming (SSE).
    Returns text/event-stream with JSON events:
    - transcription
    - text
    - audio
    """
    from fastapi.responses import StreamingResponse
    from app.services.voice_service import VoiceService
 
    # Read audio bytes
    audio_bytes = await audio.read()

    # Load chart (read-only)
    repo = KundaliCoreRepository(session)
    kundali_core = await repo.get_by_id(kundali_core_id)
    if not kundali_core:
        raise HTTPException(status_code=404, detail="Kundali not found")

    kundali_chart = kundali_core.to_domain()

    service = VoiceService()

    return StreamingResponse(
        service.answer_stream(
            session=session,
            user_id=user.id,
            kundali_core_id=kundali_core_id,
            kundali_chart=kundali_chart,
            audio_bytes=audio_bytes,
        ),
        media_type="text/event-stream"
    )