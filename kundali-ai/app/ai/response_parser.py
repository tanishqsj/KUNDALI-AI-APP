import re
from typing import Dict, Any, List


CONFIDENCE_KEYWORDS = {
    "high": [
        "strongly", "very likely", "clearly indicates", "high potential"
    ],
    "medium": [
        "likely", "suggests", "points toward", "can indicate"
    ],
    "low": [
        "may", "might", "possibly", "could"
    ],
}


def parse_llm_response(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw LLM output into structured response.

    This function is intentionally tolerant:
    - Works with plain text
    - Works with bullet points
    - Works with headings
    """

    # Extract Suggestions
    suggestions = []
    if "|||SUGGESTIONS:" in raw_text:
        parts = raw_text.split("|||SUGGESTIONS:")
        raw_text_clean = parts[0].strip()
        suggestions_str = parts[1].strip()
        if suggestions_str:
             suggestions = [s.strip() for s in suggestions_str.split("|") if s.strip()]
    else:
        raw_text_clean = raw_text

    cleaned = _clean_text(raw_text_clean)

    sections = _extract_sections(cleaned)
    confidence = _infer_confidence(cleaned)

    return {
        "text": cleaned,
        "confidence": confidence,
        "sections": sections,
        "suggestions": suggestions,
    }


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """
    Normalize whitespace and remove noise.
    """
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _extract_sections(text: str) -> List[Dict[str, str]]:
    """
    Extract titled sections if present.

    Supports:
    - Markdown-style headers
    - Colon-based titles
    """

    sections: List[Dict[str, str]] = []

    # Pattern: Title: content
    pattern = re.compile(
        r"(?P<title>[A-Z][A-Za-z\s]{3,50}):\s*(?P<body>.+?)(?=\n[A-Z][A-Za-z\s]{3,50}:|\Z)",
        re.DOTALL,
    )

    matches = pattern.finditer(text)

    for match in matches:
        title = match.group("title").strip()
        body = match.group("body").strip()
        sections.append(
            {
                "title": title,
                "content": body,
            }
        )

    return sections


def _infer_confidence(text: str) -> str:
    """
    Infer confidence level from language.
    """

    lowered = text.lower()

    for level, keywords in CONFIDENCE_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                return level

    # Default (safe)
    return "medium"
