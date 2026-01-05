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
    ) -> Dict[str, Any]:
        """
        Generate an AI answer grounded in astrology facts.
        """

        # ─────────────────────────────────────────────
        # 1. Build grounded context
        # ─────────────────────────────────────────────

        prompt_builder = self._select_prompt_builder(question)

        prompt = prompt_builder(
            question=question,
            kundali=kundali_chart.model_dump(),
            explanations=explanations,
            transits=transits,
        )

        # ─────────────────────────────────────────────
        # 2. Call LLM
        # ─────────────────────────────────────────────

        raw_response = await self.llm.complete(
            system_prompt=prompt["system"],
            user_prompt=prompt["user"],
        )

        # ─────────────────────────────────────────────
        # 3. Guardrails
        # ─────────────────────────────────────────────

        safe_response = enforce_guardrails(
            raw_response,
            question=question,
        )

        # ─────────────────────────────────────────────
        # 4. Parse structured answer
        # ─────────────────────────────────────────────

        return parse_llm_response(safe_response)

    def _select_prompt_builder(self, question: str):
        """
        Select appropriate prompt template based on question intent.
        """

        q = question.lower()

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
