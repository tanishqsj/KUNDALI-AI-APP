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
        asc_sign = kundali_chart.ascendant.sign
        moon = kundali_chart.planets["Moon"]
        moon_nak = moon.nakshatra
        moon_deg = moon.degree

        # --- Get Current Dasha for Context ---
        current_dasha_name = "Unknown"
        now_str = datetime.utcnow().isoformat()
        for d in dashas:
            if d["start_date"] <= now_str <= d["end_date"]:
                current_dasha_name = f"{d['lord']} Mahadasha"
                if "antardashas" in d:
                    for ad in d["antardashas"]:
                        if ad["start_date"] <= now_str <= ad["end_date"]:
                            current_dasha_name += f" / {ad['lord']} Antardasha"
                            break
                break

        # --- Calculate Atmakaraka & Darakaraka ---
        # Using 7-Karaka scheme (Sun to Saturn)
        karaka_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        candidates = []
        for p_name in karaka_planets:
            if p_name in kundali_chart.planets:
                p_obj = kundali_chart.planets[p_name]
                candidates.append({"name": p_name, "degree": p_obj.degree, "sign": p_obj.sign})
        
        candidates.sort(key=lambda x: x["degree"], reverse=True)
        atmakaraka = candidates[0] if candidates else None
        darakaraka = candidates[-1] if candidates else None

        # --- Context for Executive Summary ---
        mangal_present = dosha_analysis.get("mangal", {}).get("present", False)
        mangal_text = "Mangal Dosha is present" if mangal_present else "No Mangal Dosha"

        prediction_topics = {
            "Executive Summary": (
                "Create a 1-page 'Your Kundali at a Glance' Executive Summary. "
                "Strictly follow this format with these exact headers (do not use emojis):\n\n"
                "**Your Kundali at a Glance**\n"
                "**Core Identity**\n"
                f"Ascendant: {asc_sign} - [Provide 3 keywords]\n"
                f"Moon Sign: {moon.sign} - [Provide 3 keywords]\n"
                "Dominant Planetary Influence: [Identify strongest planet] ([Keywords])\n\n"
                "**Key Strengths**\n"
                "[List 3 key strengths using standard hyphens -]\n\n"
                "**Key Challenges**\n"
                "[List 3 key challenges using standard hyphens -]\n\n"
                "**Career Snapshot**\n"
                "[2-3 sentences on career direction]\n\n"
                "**Relationships & Partnerships**\n"
                f"[2-3 sentences on relationships. Mention {mangal_text}]\n\n"
                "**Current Timing**\n"
                f"{current_dasha_name}\n"
                "[Brief summary of this period]\n\n"
                "Use standard hyphens (-) for bullet points. Do not use emojis."
            ),
            "Your Ascendant": (
                f"My Ascendant is {asc_sign}. "
                "Include the following points: "
                "1. What is Ascendant? "
                f"2. State 'Your Ascendant is {asc_sign}'. "
                "3. Health. "
                "4. Temperament and Personality. "
                "5. Physical Appearance."
            ),
            "Your Nakshatra": (
                f"My Moon is in {moon_nak} Nakshatra at {moon_deg:.2f} degrees. "
                "Include the following points: "
                "1. What is Nakshatra in astrology? "
                f"2. State 'Your Nakshatra is {moon_nak}' (mention the Pada if you can calculate it from the degree). "
                "3. Nakshatra prediction: General traits, personality, how they live life, tackle problems, unique qualities, strengths, and weaknesses (areas of improvement). "
                "4. Friendships and Speciality. "
                "5. Education and Income. "
                "6. Family Life."
            ),
            "Atmakaraka": (
                f"My Atmakaraka planet is {atmakaraka['name']} at {atmakaraka['degree']:.2f} degrees in {atmakaraka['sign']}. "
                "Include the following points: "
                "1. What is Atmakaraka? (Explain it is the planet with the highest degree, representing the soul). "
                "2. How to find it in the chart? "
                "3. What effect does it have on my personality, life purpose, and spiritual growth?"
            ) if atmakaraka else "Explain Atmakaraka generally.",
            "Darakaraka": (
                f"My Darakaraka planet is {darakaraka['name']} at {darakaraka['degree']:.2f} degrees in {darakaraka['sign']}. "
                "Include the following points: "
                "1. What is Darakaraka? (Explain it is the planet with the lowest degree, representing the spouse/partner). "
                "2. How to find it in the chart? "
                "3. What effect does it have on my relationships and the personality of my potential partner?"
            ) if darakaraka else "Explain Darakaraka generally.",
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

        # --- Add Technical Analysis Topics ---
        
        # 1. House Analysis
        house_context = ""
        if kundali_derived and getattr(kundali_derived, 'house_strengths', None):
            strong_houses = []
            # Map strengths to new labels for AI Context
            strength_map = {
                "Very Strong": "Supportive",
                "Strong": "Supportive",
                "Neutral": "Neutral",
                "Weak": "Challenging",
                "Very Weak": "Challenging"
            }
            for h_key, h_data in kundali_derived.house_strengths.items():
                raw_strength = h_data.get('strength') if isinstance(h_data, dict) else None
                mapped = strength_map.get(raw_strength, "Neutral")
                
                if mapped == "Supportive":
                    strong_houses.append(f"House {h_key}")
            
            if strong_houses:
                house_context = f" Context: The following houses are Supportive in the chart: {', '.join(strong_houses)}."
        
        prediction_topics["House Analysis"] = f"Analyze the strength of the houses in my chart.{house_context}"

        # 2. Planetary Analysis
        prediction_topics["Planetary Analysis"] = "Analyze the overall strength and condition of the major planets in my chart."

        # 3. Divisional Charts (D9, D10)
        div_context = ""
        if kundali_divisionals:
            d9 = next((d for d in kundali_divisionals if d.chart_type == 'D9'), None)
            if d9 and d9.chart_data:
                asc = d9.chart_data.get('ascendant', {}).get('sign', 'Unknown')
                div_context += f" In Navamsa (D9), Ascendant is {asc}."
            
            d10 = next((d for d in kundali_divisionals if d.chart_type == 'D10'), None)
            if d10 and d10.chart_data:
                asc = d10.chart_data.get('ascendant', {}).get('sign', 'Unknown')
                div_context += f" In Dasamsa (D10), Ascendant is {asc}."
        
        prediction_topics["Divisional Charts"] = (
            f"Explain the significance of the Divisional Charts. "
            f"Specifically analyze the Navamsa (D9) for marriage/inner-self and Dasamsa (D10) for career if available. "
            f"Context:{div_context}"
        )

        # 4. Dasha Analysis
        prediction_topics["Dasha Analysis"] = "Analyze the current Vimshottari Dasha period and its implications."

        if include_transits:
            prediction_topics["Transits & Gochar"] = "How are the current planetary transits (Gochar) impacting me right now?"

        async def get_prediction(topic, question):
            # Append formatting instructions to ensure clean output
            formatted_question = (
                f"{question}\n\n"
                f"Context: Ascendant is {asc_sign}, Moon is in {moon.sign}. Current Period: {current_dasha_name}.\n"
                "Style Instructions:\n"
                "1. Use standard hyphens (-) for bullet points. Do NOT use special bullet characters or emojis.\n"
                "2. **Synthesis Rule**: Do not explain any placement in isolation. Always connect it to house, dasha, or ascendant (e.g., 'With Moon in Gemini in the 4th house...').\n"
                "3. Avoid generic filler ('Your chart suggests...').\n"
                "4. Use progressive summarization: if a fact (like Ascendant) was mentioned earlier, refer to it briefly.\n"
                "5. **Mangal Dosha Rule**: If Mangal Dosha is present, explain it fully ONLY in the 'Relationships' or 'Dosha' section. In other sections, refer to it briefly as 'Mars influence' without repeating the full definition.\n"
                "6. Separate sections with double newlines.\n"
                "7. Do NOT use markdown headers (like #, ##, ###). Use **Bold** for section headings."
            )
            ai_answer = await self.ai_service.answer(
                user_id=user_id,
                question=formatted_question,
                kundali_chart=kundali_chart,
                explanations=explanations,
                transits=transits_payload,
            )
            # Safely extract text, default to an empty string if keys are missing
            answer_text = ai_answer.get('text', 'Could not generate prediction for this topic.')
            
            # Filter: Clean up markdown headers if present
            cleaned_lines = []
            for line in answer_text.split('\n'):
                sline = line.strip()
                if sline.startswith('#'):
                    # Convert "### Title" to "**Title**"
                    content = sline.lstrip('#').strip()
                    # Avoid double bolding if AI did "**### Title**"
                    content = content.replace('**', '') 
                    cleaned_lines.append(f"**{content}**")
                else:
                    cleaned_lines.append(line)
            answer_text = "\n".join(cleaned_lines)
            
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
