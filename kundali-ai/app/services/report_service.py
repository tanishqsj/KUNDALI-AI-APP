from typing import Dict, Any, Optional
from uuid import UUID
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.kundali.calculator import KundaliCalculator
from app.persistence.repositories.birth_profile_repo import BirthProfileRepository
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.persistence.repositories.kundali_derived_repo import KundaliDerivedRepository
from app.persistence.repositories.kundali_divisional_repo import KundaliDivisionalRepository

from app.services.rule_service import RuleService
from app.services.explanation_service import ExplanationService
from app.services.transit_service import TransitService
from app.services.ai_service import AIService


class ReportService:
    """
    Builds a deterministic report context.
    """

    def __init__(self):
        self.rule_service = RuleService()
        self.explanation_service = ExplanationService()
        self.transit_service = TransitService()
        self.ai_service = AIService()
        self.calculator = KundaliCalculator()

    async def build_report_context(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        kundali_core_id: UUID,
        kundali_chart,
        include_transits: bool = False,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:

        birth_repo = BirthProfileRepository(session)
        core_repo = KundaliCoreRepository(session)
        derived_repo = KundaliDerivedRepository(session)
        divisional_repo = KundaliDivisionalRepository(session)

        kundali_core = await core_repo.get_by_id(kundali_core_id)
        birth_profile = await birth_repo.get_by_id(kundali_core.birth_profile_id)
        kundali_derived = await derived_repo.get_by_core_id(kundali_core_id)
        kundali_divisionals = await divisional_repo.get_by_core_id(kundali_core_id)

        # Calculate Vimshottari Dasha
        # Need Moon's degree and Birth Date
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

        # Calculate Avakahada Chakra
        avakahada = self.calculator.calculate_avakahada_chakra(
            moon_sign=kundali_chart.planets["Moon"].sign,
            moon_degree=kundali_chart.planets["Moon"].degree
        )

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

        transits_payload = None # Must be defined before AI call
        if include_transits:
            transits_payload = await self.transit_service.get_current(
                kundali_core_id=kundali_core_id,
                kundali_chart=kundali_chart,
                timestamp=timestamp,
            )
        
        # --- Generate AI Predictions ---
        prediction_topics = {
            "Character": "Describe my character and personality based on my chart.",
            "Happiness and Fulfillment": "What are the sources of happiness and fulfillment in my life according to my chart?",
            "Lifestyle": "What kind of lifestyle is suggested by my astrological chart?",
            "Career": "Provide a general overview of my career path and profession.",
            "Occupation": "What are some suitable occupations for me based on my chart?",
            "Health": "What are the general tendencies for my health and well-being? Do not give medical advice.",
            "Hobbies": "What hobbies and interests might I enjoy based on my chart?",
            "Finance": "What is the outlook for my finances and wealth accumulation?",
            "Education": "What does my chart say about my education and learning style?",
        }

        async def get_prediction(topic, question):
            ai_answer = await self.ai_service.answer(
                user_id=user_id,
                question=question,
                kundali_chart=kundali_chart,
                explanations=explanations,
                transits=transits_payload,
            )
            # Safely extract text, default to an empty string if keys are missing
            answer_text = ai_answer.get('text', 'Could not generate prediction for this topic.')
            return topic, answer_text

        tasks = [get_prediction(topic, q) for topic, q in prediction_topics.items()]
        prediction_results = await asyncio.gather(*tasks)
        ai_predictions = dict(prediction_results)

        return {
            "meta": {
                "generated_at": datetime.utcnow().isoformat(),
                "include_transits": include_transits,
            },
            "birth_details": {
                "name": birth_profile.name,
                "birth_date": birth_profile.birth_date.isoformat(),
                "birth_time": birth_profile.birth_time.isoformat(),
                "birth_place": birth_profile.birth_place,
                "latitude": birth_profile.latitude,
                "longitude": birth_profile.longitude,
                "timezone": birth_profile.timezone,
            },
            "kundali": kundali_chart.model_dump(),
            "persisted": {
                "core": kundali_core.to_dict(),
                "derived": kundali_derived.to_dict(),
                 "divisionals": {
                    d.chart_type: d.chart_data
                    for d in kundali_divisionals
                },
            },
            "explanations": explanations,
            "transits": transits_payload,
            "dashas": dashas,
            "sade_sati": sade_sati,
            "dosha_analysis": dosha_analysis,
            "avakahada": avakahada,
            "ai_predictions": ai_predictions,
        }
