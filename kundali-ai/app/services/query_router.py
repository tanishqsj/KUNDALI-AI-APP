# Placeholder for kundali-ai/app/services/query_router.py
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


from app.cache.query_cache import QueryCache
from app.domain.kundali.calculator import KundaliCalculator
from app.persistence.repositories.birth_profile_repo import BirthProfileRepository
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.services.rule_service import RuleService
from app.services.explanation_service import ExplanationService
from app.services.ai_service import AIService
from app.services.transit_service import TransitService


class QueryRouter:
    """
    Routes user questions to rules, transits, and/or AI
    in a controlled and explainable manner.
    """

    RULE_KEYWORDS = {
        "career", "job", "profession",
        "marriage", "relationship",
        "health", "disease",
        "finance", "money",
        "dosha", "yoga", "strength",
    }

    TRANSIT_KEYWORDS = {
        "now", "currently", "today",
        "this year", "this month",
        "next month", "next year",
        "transit", "gochar",
    }

    def __init__(self):
        self.rule_service = RuleService()
        self.explanation_service = ExplanationService()
        self.ai_service = AIService()
        self.transit_service = TransitService()
        self.cache = QueryCache()
        self.calculator = KundaliCalculator()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def answer(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        question: str,
    ) -> Dict[str, Any]:
        """
        Route and answer a user question.
        """
        cached = await self.cache.get_answer(
        user_id=user_id,
        kundali_core_id=kundali_core_id,
        question=question,
        )

        if cached:
            return cached

        intent = self._detect_intent(question)

        # ─────────────────────────────────────────────
        # 0. Calculate Derived Data (Dashas, Doshas, etc.)
        # ─────────────────────────────────────────────
        core_repo = KundaliCoreRepository(session)
        birth_repo = BirthProfileRepository(session)

        # We need birth date for Dasha calculation
        kundali_core = await core_repo.get_by_id(kundali_core_id)
        birth_profile = await birth_repo.get_by_id(kundali_core.birth_profile_id)

        # Calculate Vimshottari Dasha
        dashas = self.calculator.calculate_vimshottari_dasha(
            moon_degree=kundali_chart.planets["Moon"].degree,
            birth_date=birth_profile.birth_date,
        )

        # Calculate Sade Sati Status
        sade_sati = self.calculator.calculate_sade_sati(
            natal_moon_sign=kundali_chart.planets["Moon"].sign,
            check_date=datetime.utcnow().date()
        )

        # Calculate Specific Doshas
        dosha_analysis = {
            "mangal": self.calculator.calculate_mangal_dosha(kundali_chart.planets),
            "kalsarpa": self.calculator.calculate_kalsarpa_dosha(kundali_chart.planets)
        }
        # Avakahada is less critical for chat, skipping to save tokens/time if needed, or add if desired.

        # ─────────────────────────────────────────────
        # 1. Rule evaluation (always first)
        # ─────────────────────────────────────────────

        rule_results = await self.rule_service.evaluate_for_kundali(
            session=session, 
            kundali_core_id=kundali_core_id,
            kundali_chart=kundali_chart,
        )

        explanations = await self.explanation_service.build_explanations(
            session=session, 
            kundali_core_id=kundali_core_id,
            rule_results=rule_results,
            dashas=dashas,
            sade_sati=sade_sati,
            dosha_analysis=dosha_analysis,
        )

        # ─────────────────────────────────────────────
        # 2. Transits (if required)
        # ─────────────────────────────────────────────

        transit_payload = None
        if intent["needs_transits"]:
            transit_payload = await self.transit_service.get_current(
                kundali_core_id=kundali_core_id,
                kundali_chart=kundali_chart,
            )

        # ─────────────────────────────────────────────
        # 3. AI synthesis (if required)
        # ─────────────────────────────────────────────

        if intent["needs_ai"]:
            ai_answer = await self.ai_service.answer(
                user_id=user_id,
                question=question,
                kundali_chart=kundali_chart,
                explanations=explanations,
                transits=transit_payload,
            )

            return {
                "mode": "ai",
                "answer": ai_answer,
                "explanations": explanations,
                "transits": transit_payload,
            }

        # ─────────────────────────────────────────────
        # 4. Deterministic (rules-only) answer
        # ─────────────────────────────────────────────

        result =  {
            "mode": "rules",
            "answer": explanations,
            "explanations": explanations,
            "transits": transit_payload,
        }

        await self.cache.set_answer(
        user_id=user_id,
        kundali_core_id=kundali_core_id,
        question=question,
        answer=result,
        )

        return result


    # ─────────────────────────────────────────────
    # Intent detection
    # ─────────────────────────────────────────────

    def _detect_intent(self, question: str) -> Dict[str, bool]:
        """
        Detect routing intent from question.
        """

        q = question.lower()

        needs_rules = any(k in q for k in self.RULE_KEYWORDS)
        needs_transits = any(k in q for k in self.TRANSIT_KEYWORDS)

        # AI needed if subjective / advisory language is present
        needs_ai = any(
            phrase in q
            for phrase in [
                "should i", "what does it mean",
                "will i", "can i", "advice",
                "suggest", "explain",
            ]
        )

        # Safety: rules-only questions still get AI if vague
        if not needs_rules:
            needs_ai = True

        return {
            "needs_rules": needs_rules,
            "needs_transits": needs_transits,
            "needs_ai": needs_ai,
        }
