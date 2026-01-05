# Placeholder for kundali-ai/app/ai/prompt_templates/timing.py
from typing import Dict, Any, List, Optional
from app.ai.prompt_templates.base import build_base_prompt


def build_timing_prompt(
    *,
    question: str,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Timing / transit-focused astrology prompt.
    """

    base = build_base_prompt(
        question=question,
        kundali=kundali,
        explanations=explanations,
        transits=transits,
    )

    base["system"] += (
        "\n\nTIMING FOCUS (Vedic Astrology):\n"
        "- Prioritize the Vimshottari Dasha (Mahadasha/Antardasha) provided in the insights.\n"
        "- Use Transits (Gochar) to refine the timing of the Dasha effects.\n"
        "- Use transits only if provided.\n"
        "- Speak in windows and phases, not exact dates.\n"
        "- Avoid deterministic timing statements.\n"
    )

    return base
