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
    match_id: UUID | None = None,
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

    # Load Match Context (if match_id provided)
    match_context = None
    if match_id:
        from app.persistence.repositories.kundali_match_repo import KundaliMatchRepository
        match_repo = KundaliMatchRepository(session)
        match_result = await match_repo.get_by_id(match_id)
        
        if match_result:
            boy_kundali = await repo.get_by_id(match_result.boy_kundali_id)
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

    service = VoiceService()

    return StreamingResponse(
        service.answer_stream(
            session=session,
            user_id=user.id,
            kundali_core_id=kundali_core_id,
            kundali_chart=kundali_chart,
            audio_bytes=audio_bytes,
            audio_filename=audio.filename or "audio.wav",
            match_context=match_context,
        ),
        media_type="text/event-stream"
    )