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

    # ─────────────────────────────────────────────
    # Internal stubs (replace later)
    # ─────────────────────────────────────────────

    def _speech_to_text_stub(
        self,
        *,
        audio_bytes: bytes,
        language: str,
    ) -> str:
        """
        Placeholder for Whisper / speech-to-text.
        """
        return "What does my career look like?"

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
