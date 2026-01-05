# Placeholder for kundali-ai/app/ai/prompt_templates/relationship.py
from typing import Dict, Any, List, Optional
from app.ai.prompt_templates.base import build_base_prompt


def build_relationship_prompt(
    *,
    question: str,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Relationship & marriage-focused astrology prompt.
    """

    base = build_base_prompt(
        question=question,
        kundali=kundali,
        explanations=explanations,
        transits=transits,
    )

    base["system"] += (
        "\n\nRELATIONSHIP FOCUS (Vedic Astrology):\n"
        "- Analyze the 7th House, its Lord, and planets in it.\n"
        "- Consider Venus (Shukra) as the Karaka for relationships.\n"
        "- Discuss emotional patterns, communication, compatibility themes.\n"
        "- Avoid certainty about marriage/divorce timelines.\n"
        "- Emphasize mutual effort and awareness.\n"
    )

    return base
