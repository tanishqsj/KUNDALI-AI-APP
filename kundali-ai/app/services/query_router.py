# Placeholder for kundali-ai/app/services/query_router.py
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


from app.cache.query_cache import QueryCache
from app.domain.kundali.calculator import KundaliCalculator
from app.persistence.repositories.birth_profile_repo import BirthProfileRepository
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.persistence.repositories.kundali_derived_repo import KundaliDerivedRepository
from app.persistence.repositories.kundali_divisional_repo import KundaliDivisionalRepository
from app.services.rule_service import RuleService
from app.services.explanation_service import ExplanationService
from app.services.ai_service import AIService
from app.services.transit_service import TransitService
from app.services.knowledge_service import KnowledgeService


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
        self.knowledge_service = KnowledgeService()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def _generate_cache_key(self, kundali_id: UUID, question: str, language: str) -> str:
        import hashlib
        import re
        # Normalize: alphanumeric only, lowercase, single spaces
        # This fixes "Voice vs Text" cache misses (e.g. "Who am I" vs "Who am I?")
        normalized_q = re.sub(r'[^\w\s]', '', question).lower()
        normalized_q = re.sub(r'\s+', ' ', normalized_q).strip()

        q_hash = hashlib.md5(normalized_q.encode("utf-8")).hexdigest()
        return f"answer:{kundali_id}:{q_hash}:{language}"

    async def stream_answer(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        question: str,
        language: str = "English",
        ttl: int = 86400, # 24 Hours
    ):
        """
        Stream answer directly from AI Service, with Caching.
        """
        import json
        from app.cache.redis import RedisClient

        # 0. Generate Cache Key
        cache_key = self._generate_cache_key(kundali_core_id, question, language)

        # 1. Check Cache
        try:
            redis_client = RedisClient.get_client()
            cached_answer = await redis_client.get(cache_key)
            if cached_answer:
                import asyncio
                # Simulate streaming for consistent UX (Fast Typewriter)
                words = cached_answer.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield json.dumps({"chunk": chunk}) + "\n"
                    # 10ms delay gives ~100 words/sec (very fast reading speed but visible stream)
                    await asyncio.sleep(0.01)
                return
        except Exception as e:
            print(f"⚠️ [Redis] Read failed: {e}")

        # 2. Retrieve RAG Context (Only if Cache Miss)
        rag_context = await self.knowledge_service.retrieve_context(
            session=session,
            query=question
        )

        explanations = []

        # 3. Stream from AI Service & Accumulate
        full_text_accumulator = ""
        
        async for chunk in self.ai_service.stream_answer(
            user_id=user_id,
            question=question,
            kundali_chart=kundali_chart,
            explanations=explanations,
            rag_context=rag_context,
            language=language or "English"
        ):
            # Parse chunk ... (same)
            try:
                clean_chunk = chunk.strip() 
                if clean_chunk:
                    data = json.loads(clean_chunk)
                    if "chunk" in data:
                         full_text_accumulator += data["chunk"]
            except:
                pass

            yield chunk

        # 4. Save to Cache
        if full_text_accumulator:
            try:
                await redis_client.setex(cache_key, ttl, full_text_accumulator)
            except Exception as e:
                print(f"⚠️ [Redis] Write failed: {e}")

    async def answer(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        question: str,
        language: str = "English",
    ) -> Dict[str, Any]:
        """
        Route and answer a user question.
        """
        from app.cache.redis import RedisClient
        
        # 1. Check Shared Cache (Redis)
        cache_key = self._generate_cache_key(kundali_core_id, question, language)
        try:
            redis_client = RedisClient.get_client()
            cached_text = await redis_client.get(cache_key)
            if cached_text:
                # Construct a mock response from cached text
                return {
                    "mode": "ai",
                    "answer": {"text": cached_text, "language": language},
                    "suggestions": [],
                    "explanations": [],
                    "transits": None,
                    "rag_sources": 0, # Cached
                }
        except Exception as e:
             print(f"⚠️ [Redis] Read failed in answer: {e}")

        # Legacy Cache Check (Optional, keeping for safety if Redis fails or different key used)
        cached = await self.cache.get_answer(
            user_id=user_id,
            kundali_core_id=kundali_core_id,
            question=question,
        )
        if cached:
            return cached

        # ... (Rest of logic) ...

        intent = self._detect_intent(question)

        # ─────────────────────────────────────────────
        # 0. Calculate Derived Data (Dashas, Doshas, etc.)
        # ─────────────────────────────────────────────
        core_repo = KundaliCoreRepository(session)
        birth_repo = BirthProfileRepository(session)
        derived_repo = KundaliDerivedRepository(session)
        divisional_repo = KundaliDivisionalRepository(session)

        # We need birth date for Dasha calculation
        kundali_core = await core_repo.get_by_id(kundali_core_id)
        birth_profile = await birth_repo.get_by_id(kundali_core.birth_profile_id)
        kundali_derived = await derived_repo.get_by_core_id(kundali_core_id)
        kundali_divisionals = await divisional_repo.get_by_core_id(kundali_core_id)

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

        avakahada = self.calculator.calculate_avakahada_chakra(
            moon_sign=kundali_chart.planets["Moon"].sign,
            moon_degree=kundali_chart.planets["Moon"].degree
        )

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
            avakahada=avakahada,
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
        #Retrieve Context from Knowledge Base
        rag_context = []
        if intent["needs_ai"]:
            # We pass 'session' because the Repo needs it
            rag_context = await self.knowledge_service.retrieve_context(
                session=session, 
                query=question, 
                limit=5
            )

        if intent["needs_ai"]:
            ai_answer = await self.ai_service.answer(
                user_id=user_id,
                question=question,
                kundali_chart=kundali_chart,
                explanations=explanations,
                transits=transit_payload,
                derived=kundali_derived.to_dict() if kundali_derived else None,
                divisionals=kundali_divisionals,
                rag_context=rag_context,
                language=language, # <--- Pass language to AI Service
            )

            # SAVE TO SHARED REDIS CACHE
            try:
                text_to_cache = ai_answer.get("text") or str(ai_answer)
                if isinstance(text_to_cache, str) and text_to_cache.strip():
                     await redis_client.setex(cache_key, 86400, text_to_cache)
            except Exception as e:
                print(f"⚠️ [Redis] Shared cache write failed (Voice path): {e}")

            return {
                "mode": "ai",
                "answer": ai_answer,
                "suggestions": ai_answer.get("suggestions", []),
                "explanations": explanations,
                "transits": transit_payload,
                "rag_sources": len(rag_context),
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

        needs_ai = True

        return {
            "needs_rules": needs_rules,
            "needs_transits": needs_transits,
            "needs_ai": needs_ai,
        }
