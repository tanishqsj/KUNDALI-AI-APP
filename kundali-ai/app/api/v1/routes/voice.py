from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
import base64
import os
from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.persistence.db import get_db_session
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.services.query_router import QueryRouter

router = APIRouter()

@router.post("/voice")
async def voice_interaction(
    kundali_core_id: UUID,
    audio: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Handle voice input: STT -> Query AI -> TTS -> Return Audio/Text
    """
    # 1. Read Audio & STT (Speech-to-Text)
    audio_content = await audio.read()

    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        question_text = "Error: OPENAI_API_KEY is not set."
    else:
        try:
            client = AsyncOpenAI(api_key=api_key)
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio.filename or "audio.wav", audio_content, audio.content_type or "audio/wav")
            )
            question_text = transcription.text
        except OpenAIError as e:
            question_text = f"Error during transcription: {e}"
        except Exception as e:
            question_text = f"Unexpected transcription error: {e}"
    
    # 2. Fetch Kundali
    repo = KundaliCoreRepository(session)
    kundali_core = await repo.get_by_id(kundali_core_id)
    if not kundali_core:
        raise HTTPException(status_code=404, detail="Kundali not found")
    
    kundali_chart = kundali_core.to_domain()

    # 3. Process Query via AI/Rules
    query_router = QueryRouter()
    user_id = uuid4() # Mock user ID
    
    answer_data = await query_router.answer(
        session=session,
        user_id=user_id,
        kundali_core_id=kundali_core_id,
        kundali_chart=kundali_chart,
        question=question_text
    )
    
    # Extract text answer
    answer_text = "I processed your request."
    if answer_data.get("mode") == "ai" and isinstance(answer_data.get("answer"), dict):
        answer_text = answer_data["answer"].get("text", str(answer_data["answer"]))
    elif answer_data.get("mode") == "rules":
        answer_text = "I found relevant astrological rules in your chart."

    # 4. Mock TTS (Text-to-Speech)
    # Echoing the input audio back so you can hear that it was recorded successfully.
    audio_bytes = audio_content
    
    return {
        "question_text": question_text,
        "answer_text": answer_text,
        "audio_bytes": base64.b64encode(audio_bytes).decode('utf-8')
    }