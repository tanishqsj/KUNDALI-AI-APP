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
    detected_language = "English"

    if not api_key:
        question_text = "Error: OPENAI_API_KEY is not set."
    else:
        try:
            client = AsyncOpenAI(api_key=api_key)
            # Use verbose_json to get language info
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio.filename or "audio.wav", audio_content, audio.content_type or "audio/wav"),
                response_format="verbose_json",
                prompt="Hindi Marathi English astrology query"
            )
            question_text = transcription.text
            # Map Whisper language code to full name for AI prompt
            lang_map = {"hi": "Hindi", "en": "English", "mr": "Marathi"}
            detected_language = lang_map.get(transcription.language, "English")
            
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

        question=question_text,
        language=detected_language 
    )
    
    # Extract text answer
    answer_text = "I processed your request."
    if answer_data.get("mode") == "ai" and isinstance(answer_data.get("answer"), dict):
        answer_text = answer_data["answer"].get("text", str(answer_data["answer"]))
    elif answer_data.get("mode") == "rules":
        answer_text = "I found relevant astrological rules in your chart."

    # Extract Suggestions
    suggestions = []
    if "|||SUGGESTIONS:" in answer_text:
        parts = answer_text.split("|||SUGGESTIONS:")
        answer_text = parts[0].strip()
        if len(parts) > 1:
            suggestions = [s.strip() for s in parts[1].split("|") if s.strip()]

    # 4. Real TTS (Edge-TTS - Free)
    # Generate audio from the answer text
    try:
        # Clean text for TTS (remove Markdown)
        tts_text = re.sub(r'\*+', '', answer_text) # Remove asterisks
        tts_text = re.sub(r'#+', '', tts_text)     # Remove hashes
        tts_text = re.sub(r'[\[\]]', '', tts_text) # Remove brackets
        
        # Select Voice based on Language or Content
        voice = "en-IN-NeerjaNeural"
        if detected_language == "Marathi":
             voice = "mr-IN-AarohiNeural"
        elif detected_language == "Hindi":
             voice = "hi-IN-SwaraNeural"
        elif any('\u0900' <= char <= '\u097f' for char in answer_text):
             # Fallback for Devanagari text if language wasn't explicitly detected
             # Check for Marathi-specific character 'ळ' (U+0933)
             if '\u0933' in answer_text:
                 voice = "mr-IN-AarohiNeural"
             else:
                 voice = "hi-IN-SwaraNeural"

        print(f"DEBUG: Generating TTS. Voice: {voice}, Text Preview: {tts_text[:50]}...")

        communicate = edge_tts.Communicate(tts_text, voice)
        # Edge-TTS is async and writes to stream
        # We capture it in memory
        fp = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                fp.write(chunk["data"])
        
        audio_bytes = fp.getvalue()
        print(f"DEBUG: TTS Complete. Bytes: {len(audio_bytes)}")

    except Exception as e:
        print(f"TTS Error: {e}")
        audio_bytes = b""

    return {
        "question_text": question_text,
        "answer_text": answer_text,
        "audio_bytes": base64.b64encode(audio_bytes).decode('utf-8'),
        "suggestions": suggestions
    }