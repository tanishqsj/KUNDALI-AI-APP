# Placeholder for kundali-ai/app/ai/guardrails.py
import re
from typing import Dict, Any


# ─────────────────────────────────────────────
# Guardrail configuration
# ─────────────────────────────────────────────

ABSOLUTE_TERMS = [
    "definitely",
    "certainly",
    "guaranteed",
    "will happen",
    "no doubt",
    "inevitable",
    "fixed outcome",
]

MEDICAL_TERMS = [
    "cancer",
    "diabetes",
    "heart attack",
    "death",
    "terminal",
    "disease",
    "diagnose",
    "cure",
]

LEGAL_TERMS = [
    "lawsuit",
    "court",
    "legal action",
    "jail",
    "crime",
]

FATALISTIC_PHRASES = [
    "nothing can be done",
    "no solution",
    "you will suffer",
    "bad fate",
    "unavoidable loss",
]


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def enforce_guardrails(
    raw_response: str,
    *,
    question: str,
) -> str:
    """
    Enforce safety, tone, and certainty guardrails
    on raw LLM output.
    """

    text = raw_response.strip()

    text = _remove_medical_claims(text)
    text = _remove_legal_claims(text)
    text = _soften_absolutes(text)
    text = _remove_fatalism(text)

    text = _append_disclaimer_if_needed(text, question)

    return text


# ─────────────────────────────────────────────
# Guardrail helpers
# ─────────────────────────────────────────────

def _remove_medical_claims(text: str) -> str:
    for term in MEDICAL_TERMS:
        pattern = re.compile(rf"\b{term}\b", re.IGNORECASE)
        if pattern.search(text):
            text = (
                "Astrology does not provide medical diagnoses or predictions. "
                "For health concerns, please consult a qualified medical professional.\n\n"
                + text
            )
            break
    return text


def _remove_legal_claims(text: str) -> str:
    for term in LEGAL_TERMS:
        pattern = re.compile(rf"\b{term}\b", re.IGNORECASE)
        if pattern.search(text):
            text = (
                "Astrology cannot replace legal advice. "
                "Please consult a qualified legal professional for such matters.\n\n"
                + text
            )
            break
    return text


def _soften_absolutes(text: str) -> str:
    for term in ABSOLUTE_TERMS:
        text = re.sub(
            rf"\b{term}\b",
            "is likely to",
            text,
            flags=re.IGNORECASE,
        )
    return text


def _remove_fatalism(text: str) -> str:
    for phrase in FATALISTIC_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        text = pattern.sub(
            "this may require conscious effort and awareness",
            text,
        )
    return text


def _append_disclaimer_if_needed(text: str, question: str) -> str:
    """
    Append a gentle disclaimer for sensitive domains.
    """

    sensitive_keywords = [
        "health",
        "disease",
        "death",
        "marriage",
        "divorce",
        "money",
        "career",
    ]

    if any(k in question.lower() for k in sensitive_keywords):
        return (
            text
            + "\n\n"
            + "_Note: Astrology offers symbolic insights and tendencies, "
              "not fixed outcomes or guarantees._"
        )

    return text
