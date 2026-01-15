from typing import Dict, Any, List
from uuid import UUID

from app.ai.llm_client import LLMClient
from app.ai.guardrails import enforce_guardrails
from app.ai.response_parser import parse_llm_response
from app.ai.prompt_templates.base import build_base_prompt
from app.ai.prompt_templates.career import build_career_prompt
from app.ai.prompt_templates.relationship import build_relationship_prompt
from app.ai.prompt_templates.health import build_health_prompt
from app.ai.prompt_templates.timing import build_timing_prompt
from app.ai.prompt_templates.remedies import build_remedies_prompt


class AIService:
    """
    Handles LLM interaction only.
    No routing, no astrology logic, no DB access.
    """

    def __init__(self):
        self.llm = LLMClient()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def answer(
        self,
        *,
        user_id: UUID,
        question: str,
        kundali_chart,
        explanations: List[Dict[str, Any]],
        transits: Dict[str, Any] | None = None,
        derived: Dict[str, Any] | None = None,
        divisionals: List[Any] | None = None,
        rag_context: List[str] | None = None,
        language: str = "English",  # <--- NEW PARAMETER
    ) -> Dict[str, Any]:
        """
        Generate an AI answer grounded in astrology facts.
        """

        # ─────────────────────────────────────────────
        # 1. Build grounded context
        # ─────────────────────────────────────────────

        prompt_builder = self._select_prompt_builder(question)

        # Sanitize chart data to send only what's necessary for astrology
        # This saves tokens and improves focus
        sanitized_chart = {
            "ascendant": {
                "sign": kundali_chart.ascendant.sign,
                "degree": round(kundali_chart.ascendant.degree, 2)
            },
            "planets": {
                name: {
                    "sign": p.sign, "house": p.house, "degree": round(p.degree, 2),
                    "nakshatra": p.nakshatra, "retrograde": p.retrograde
                }
                for name, p in kundali_chart.planets.items()
            }
        }

        # Calculate Atmakaraka & Darakaraka (7-Karaka scheme)
        karaka_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        candidates = []
        for p_name in karaka_planets:
            p_obj = kundali_chart.planets.get(p_name)
            if p_obj:
                candidates.append({"name": p_name, "degree": p_obj.degree})
        
        candidates.sort(key=lambda x: x["degree"], reverse=True)
        sanitized_chart["karakas"] = {
            "atmakaraka": candidates[0]["name"] if candidates else None,
            "darakaraka": candidates[-1]["name"] if candidates else None
        }

        # Include key divisional charts (D9 for relationships, D10 for career)
        if divisionals:
            sanitized_chart["divisionals"] = {}
            for div in divisionals:
                if div.chart_type in ["D9", "D10"]:
                    sanitized_chart["divisionals"][div.chart_type] = {
                        "ascendant": div.chart_data.get("ascendant"),
                        "planets": {
                            p_name: {"sign": p_data.get("sign"), "house": p_data.get("house")}
                            for p_name, p_data in div.chart_data.get("planets", {}).items()
                        }
                    }

        # Include strengths from derived data
        if derived:
            sanitized_chart["strengths"] = {
                "planet_strengths": {
                    k: v.get("strength") for k, v in derived.get("planet_strengths", {}).items()
                },
                "house_strengths": {
                    k: v.get("strength") for k, v in derived.get("house_strengths", {}).items()
                }
            }

        prompt = prompt_builder(
            question=question,
            kundali=sanitized_chart,
            explanations=explanations,
            transits=transits,
        )

        # ─────────────────────────────────────────────
        # 2. INJECT RAG CONTEXT
        # ─────────────────────────────────────────────

        if rag_context:
            context_str = "\n\n".join(rag_context)
            
            # 👇 THIS IS THE "MAXIMUM USE" PROMPT 👇
            additional_instructions = (
                "\n\n🛑 IMPORTANT: SHASTRA REFERENCE (RAG DATA) 🛑\n"
                "You have access to the following authentic Vedic scriptures (Shastras) retrieved specifically for this query:\n"
                "--------------------------------------------------\n"
                f"{context_str}\n"
                "--------------------------------------------------\n"
                "GUIDELINES FOR USING THIS CONTEXT:\n"
                "1. PRIORITY: This context is your Primary Source of Truth. If it conflicts with general knowledge, follow this context.\n"
                "2. CITATION: When you make a prediction based on these texts, mention the source (e.g., 'According to Phaladeepika...').\n"
                "3. APPLICATION: Apply the specific rules found in the context to the planetary positions in the provided Kundali Chart.\n"
                "4. ACCURACY: Do not hallucinate. If the context mentions a specific yoga or effect, quote it accurately.\n"
            )
            
            # Append to System Prompt (giving it high importance)
            prompt["system"] = prompt["system"] + additional_instructions
            
            # OPTIONAL: Uncomment this if you want to see the FULL prompt in logs
            # print(f"📜 [DEBUG] Final System Prompt:\n{prompt['system']}")

        # ─────────────────────────────────────────────
        # 2.5 INJECT LANGUAGE INSTRUCTION
        # ─────────────────────────────────────────────
        if language and language.lower() != "english":
            language_instruction = (
                f"\n\n🌍 **LANGUAGE REQUIREMENT** 🌍\n"
                f"You MUST generate the entire response in **{language}** language.\n"
                f"Do not just translate; write naturally in {language} as an astrologer would speak.\n"
                f"Keep astrological terms (like 'Dasha', 'Lagna') in their original Sanskrit form if appropriate for {language}."
            )
            prompt["system"] = prompt["system"] + language_instruction

        # ─────────────────────────────────────────────
        # 2.6 INJECT SUGGESTION INSTRUCTION
        # ─────────────────────────────────────────────
        suggestion_instruction = (
            "\n\n🔮 **FOLLOW-UP SUGGESTIONS** 🔮\n"
            "At the very end of your response, strictly purely append a list of 3 short, relevant follow-up questions "
            "that the user might want to ask next based on your analysis.\n"
            "Use this EXACT format:\n"
            "|||SUGGESTIONS: <Question 1>|<Question 2>|<Question 3>\n"
            "Example:\n"
            "...end of answer.\n"
            "|||SUGGESTIONS: When will I get married?|Is my health okay?|Gemstone for luck?"
        )
        prompt["system"] = prompt["system"] + suggestion_instruction

        # ─────────────────────────────────────────────
        # 3. Call LLM
        # ─────────────────────────────────────────────

        raw_response = await self.llm.complete(
            system_prompt=prompt["system"],
            user_prompt=prompt["user"],
        )

        # ─────────────────────────────────────────────
        # 4. Guardrails
        # ─────────────────────────────────────────────

        safe_response = enforce_guardrails(
            raw_response,
            question=question,
        )

        # ─────────────────────────────────────────────
        # 5. Parse structured answer
        # ─────────────────────────────────────────────

        return parse_llm_response(safe_response)

    def _select_prompt_builder(self, question: str):
        """
        Select appropriate prompt template based on question intent.
        """

        q = question.lower()

        if "comprehensive analysis" in q or "general predictions" in q:
            return build_base_prompt

        if any(k in q for k in ["job", "career", "profession", "work"]):
            return build_career_prompt

        if any(k in q for k in ["love", "relationship", "marriage", "partner"]):
            return build_relationship_prompt

        if any(k in q for k in ["health", "stress", "energy", "wellbeing"]):
            return build_health_prompt

        if any(k in q for k in ["when", "timing", "this year", "next", "transit"]):
            return build_timing_prompt

        if any(k in q for k in ["remedy", "solution", "advice", "what should i do"]):
            return build_remedies_prompt

        return build_base_prompt