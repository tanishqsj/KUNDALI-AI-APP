# Placeholder for kundali-ai/app/domain/rules/schemas.py
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Atomic Conditions
# ─────────────────────────────────────────────

class PlanetCondition(BaseModel):
    """
    Condition based on a planet's placement.
    """
    entity: Literal["planet"] = "planet"
    name: str = Field(..., description="Planet name (e.g., Jupiter)")
    house: Optional[int] = Field(None, description="House number (1–12)")
    sign: Optional[str] = Field(None, description="Zodiac sign")


class HouseCondition(BaseModel):
    """
    Condition based on house strength.
    """
    entity: Literal["house"] = "house"
    house: int
    strength: Optional[str] = Field(None, description="strong / average / weak")


class DoshaCondition(BaseModel):
    """
    Condition based on presence of a dosha.
    """
    entity: Literal["dosha"] = "dosha"
    name: str
    present: bool = True


AtomicCondition = PlanetCondition | HouseCondition | DoshaCondition


# ─────────────────────────────────────────────
# Logical Combinators
# ─────────────────────────────────────────────

class AllCondition(BaseModel):
    """
    All subconditions must match.
    """
    all: List[AtomicCondition]


class AnyCondition(BaseModel):
    """
    Any one of the subconditions must match.
    """
    any: List[AtomicCondition]


RuleCondition = AllCondition | AnyCondition


# ─────────────────────────────────────────────
# Rule Effects
# ─────────────────────────────────────────────

class RuleEffect(BaseModel):
    """
    Represents the outcome when a rule matches.
    """
    category: str = Field(
        ...,
        description="career, marriage, health, finance, etc."
    )
    impact: str = Field(
        ...,
        description="positive / neutral / negative"
    )
    tags: List[str] = Field(default_factory=list)
    confidence: Optional[str] = Field(
        None,
        description="low / medium / high"
    )
    notes: Optional[str] = None
