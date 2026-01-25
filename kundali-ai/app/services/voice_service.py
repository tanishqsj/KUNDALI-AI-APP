from typing import Dict, Any
from uuid import UUID
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.db import get_db_session
from app.services.query_router import QueryRouter
from app.services.billing_service import BillingService


class VoiceService:
    """
    Voice-based astrology service.

    Flow:
    audio → text → query_router → text answer → audio
    """

    def __init__(self):
        self.router = QueryRouter()
        self.billing_service = BillingService()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def answer(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        audio_bytes: bytes,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Answer a voice-based astrology question.
        """

        # ─────────────────────────────────────────────
        # 1. Billing check
        # ─────────────────────────────────────────────
        session: AsyncSession = Depends(get_db_session),

        self.billing_service.assert_quota(
            session=session,
            user_id=user_id,
            feature="voice",
        )

        # ─────────────────────────────────────────────
        # 2. Speech → text (stub)
        # ─────────────────────────────────────────────

        question_text = self._speech_to_text_stub(
            audio_bytes=audio_bytes,
            language=language,
        )

        # ─────────────────────────────────────────────
        # 3. Route question
        # ─────────────────────────────────────────────

        response = await self.router.answer(
            session=session,
            user_id=user_id,
            kundali_core_id=kundali_core_id,
            kundali_chart=kundali_chart,
            question=question_text,
        )

        # ─────────────────────────────────────────────
        # 4. Text → speech (stub)
        # ─────────────────────────────────────────────

        audio_response = self._text_to_speech_stub(
            text=self._extract_answer_text(response),
            language=language,
        )

        # ─────────────────────────────────────────────
        # 5. Log usage
        # ─────────────────────────────────────────────

        self.billing_service.log_usage(
            session=session,
            user_id=user_id,
            feature="voice",
        )

        return {
            "question_text": question_text,
            "answer_text": response,
            "audio_bytes": audio_response,
            "content_type": "audio/wav",
        }

    async def answer_stream(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        audio_bytes: bytes,
        language: str = "en",
        match_context: Dict[str, Any] | None = None,
    ):
        """
        Stream voice interaction (SSE format).
        Events:
        - data: {"type": "transcription", "text": "..."}
        - data: {"type": "text", "chunk": "..."}
        - data: {"type": "audio", "chunk": "<base64>"}
        """
        import json
        import base64
        from app.services.tts_service import TTSService

        tts_service = TTSService(language=language)

        # 1. Billing check (Quick check)
        await self.billing_service.assert_quota(
            session=session,
            user_id=user_id,
            feature="voice",
        )

        # 2. Speech → text (Real Whisper)
        question_text = await self._speech_to_text_stub(
            audio_bytes=audio_bytes,
            language=language,
        )

        # Yield Transcription
        yield json.dumps({"type": "transcription", "text": question_text}) + "\n"

        # 3. Route question & Stream Answer
        
        # Buffer for TTS
        tts_buffer = ""
        delimiters = {".", "?", "!", ":", ";", "\n"}

        async for text_chunk in self.router.stream_answer(
            session=session,
            user_id=user_id,
            kundali_core_id=kundali_core_id,
            kundali_chart=kundali_chart,
            question=question_text,
            language=language,
            match_context=match_context,
        ):
            # Parse the router chunk (which is json: {"chunk": "..."})
            try:
                data = json.loads(text_chunk)
                if "chunk" in data:
                    token = data["chunk"]
                    
                    # Yield Text Event to Client
                    yield json.dumps({"type": "text", "chunk": token}) + "\n"

                    # Accumulate for TTS (Cleaned)
                    tts_buffer += self._clean_text_for_tts(token)

            except Exception:
                pass

        # 4. Generate Full Audio (No gaps)
        print(f"[VoiceService] Buffering complete. Text length: {len(tts_buffer)}")
        if tts_buffer.strip():
             try:
                 # Generate Audio and Timings
                 print("[VoiceService] Calling TTSService...")
                 audio_bytes, timings = await tts_service.generate_audio(tts_buffer.strip())
                 print(f"[VoiceService] TTS Complete. Audio size: {len(audio_bytes) if audio_bytes else 0}, Timings: {len(timings)}")
                 
                 if audio_bytes:
                    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    
                    # Yield Timings FIRST so frontend can prepare
                    yield json.dumps({"type": "timings", "data": timings}) + "\n"
                    
                    # Yield Audio in Chunks (32KB) to prevent packet splitting issues
                    chunk_size = 32768 # Must be multiple of 4 for valid Base64 splits
                    for i in range(0, len(b64_audio), chunk_size):
                        chunk = b64_audio[i:i + chunk_size]
                        yield json.dumps({"type": "audio", "chunk": chunk}) + "\n"
                 else:
                     print("[VoiceService] WARNING: No audio bytes returned from TTS.")
             except Exception as e:
                 print(f"[VoiceService] TTS Error: {e}")
                 import traceback
                 traceback.print_exc()

        # 4. Log usage
        await self.billing_service.log_usage(
            session=session,
            user_id=user_id,
            feature="voice",
        )


    async def _speech_to_text_stub(
        self,
        *,
        audio_bytes: bytes,
        language: str,
    ) -> str:
        """
        Real Speech-to-Text using OpenAI Whisper.
        """
        import io
        from openai import AsyncOpenAI
        from app.config import settings

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Create a file-like object
        # OpenAI API expects a tuple (filename, file, content_type)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav" 

        try:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language != "en" else None # Auto-detect for english or if not specified
            )
            return transcript.text
        except Exception as e:
            print(f"STT Error: {e}")
            return "Could not understand audio."

    def _text_to_speech_stub(
        self,
        *,
        text: str,
        language: str,
    ) -> bytes:
        """
        Placeholder for TTS engine.
        """
        return f"VOICE_RESPONSE: {text}".encode("utf-8")

    def _extract_answer_text(
        self,
        response: Dict[str, Any],
    ) -> str:
        """
        Extract plain text from router response.
        """
        if response.get("mode") == "ai":
            return response["answer"].get("text", "")
        return str(response["answer"])

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Remove markdown symbols (*, #, etc.) and citations like [doc1] 
        so TTS doesn't read them out.
        """
        import re
        # Remove bold/italic markers
        text = text.replace("*", "").replace("#", "").replace("`", "")
        # Remove citations like [doc1], [1]
        text = re.sub(r"\[.*?\]", "", text)
        return text
