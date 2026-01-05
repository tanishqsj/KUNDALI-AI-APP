from typing import Dict, Any, List, Optional
import json


SYSTEM_INSTRUCTIONS = """
You are an expert Vedic Astrology (Jyotish) assistant.

IMPORTANT RULES:
- Use ONLY the provided data.
- Do NOT invent facts, placements, dates, or events.
- Do NOT give medical, legal, or absolute predictions.
- Avoid fatalistic or guaranteed language.
- Speak in probabilities, tendencies, and themes.
- Be calm, respectful, and grounded.
- If information is insufficient, say so clearly.

You must base your response strictly on:
1) Kundali facts
2) Rule-based insights (These are the calculated facts, prioritize them)
3) Transit data (if provided)

If a claim is not supported by the data, do NOT state it.
"""


def build_base_prompt(
    *,
    question: str,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Build the base system + user prompt for the LLM.
    """

    system_prompt = _build_system_prompt(
        kundali=kundali,
        explanations=explanations,
        transits=transits,
    )

    user_prompt = _build_user_prompt(question)

    return {
        "system": system_prompt,
        "user": user_prompt,
    }


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _build_system_prompt(
    *,
    kundali: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    transits: Optional[Dict[str, Any]],
) -> str:
    """
    Construct the system prompt with grounded data.
    """

    parts: List[str] = [SYSTEM_INSTRUCTIONS.strip()]

    parts.append("\n=== KUNDALI FACTS ===\n")
    parts.append(_safe_json(kundali))

    if explanations:
        parts.append("\n=== RULE-BASED INSIGHTS ===\n")
        parts.append(_safe_json(explanations))

    if transits:
        parts.append("\n=== CURRENT TRANSITS ===\n")
        parts.append(_safe_json(transits))

    return "\n".join(parts)


def _build_user_prompt(question: str) -> str:
    """
    Construct the user-facing prompt.
    """
    return f"User question:\n{question.strip()}"


def _safe_json(data: Any) -> str:
    """
    Serialize data safely for LLM consumption.
    """
    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        default=str,
    )
