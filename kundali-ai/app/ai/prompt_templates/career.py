# Placeholder for kundali-ai/app/ai/prompt_templates/career.py
from typing import Dict, Any, List, Optional
from app.ai.prompt_templates.base import build_base_prompt


def build_career_prompt(
    *,
    question: str,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Career-focused astrology prompt.
    """

    base = build_base_prompt(
        question=question,
        kundali=kundali,
        explanations=explanations,
        transits=transits,
    )

    base["system"] += (
        "\n\nCAREER FOCUS (Vedic Astrology):\n"
        "- Analyze the 10th House (Karma Bhava), its Lord, and any planets in it.\n"
        "- Consider Saturn (Shani) as the Karaka for profession.\n"
        "- Focus on profession, growth, skills, stability, and timing.\n"
        "- Avoid guarantees about promotions or income.\n"
        "- Frame outcomes as tendencies and phases.\n"
    )

    return base
