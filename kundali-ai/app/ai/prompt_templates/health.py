# Placeholder for kundali-ai/app/ai/prompt_templates/health.py
from typing import Dict, Any, List, Optional
from app.ai.prompt_templates.base import build_base_prompt


def build_health_prompt(
    *,
    question: str,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Health-safe astrology prompt.
    """

    base = build_base_prompt(
        question=question,
        kundali=kundali,
        explanations=explanations,
        transits=transits,
    )

    base["system"] += (
        "\n\nHEALTH FOCUS (Vedic Astrology):\n"
        "- Analyze the Ascendant (Lagna) and its Lord for general vitality.\n"
        "- Look at the 6th House (Rog) for tendencies, but do NOT diagnose.\n"
        "- Speak only about general vitality, stress patterns, and self-care tendencies.\n"
        "- Do NOT mention diseases, diagnoses, or outcomes.\n"
        "- Always frame health topics as lifestyle awareness, not predictions.\n"
    )

    return base
