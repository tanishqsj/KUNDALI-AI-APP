# Placeholder for kundali-ai/app/ai/prompt_templates/remedies.py
from typing import Dict, Any, List, Optional
from app.ai.prompt_templates.base import build_base_prompt


def build_remedies_prompt(
    *,
    question: str,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Remedies & advice-focused astrology prompt.
    """

    base = build_base_prompt(
        question=question,
        kundali=kundali,
        explanations=explanations,
        transits=transits,
    )

    base["system"] += (
        "\n\nREMEDIES FOCUS:\n"
        "- Suggest only gentle, non-harmful practices (reflection, discipline, habits).\n"
        "- Avoid costly, extreme, or superstitious prescriptions.\n"
        "- Frame remedies as optional supportive practices.\n"
    )

    return base
