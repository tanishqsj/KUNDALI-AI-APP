from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Atomic Derived Facts
# ─────────────────────────────────────────────

class Dosha(BaseModel):
    """
    Represents a dosha and its presence.
    """
    name: str
    present: bool
    severity: Optional[str] = None
    description: Optional[str] = None


class Yoga(BaseModel):
    """
    Represents a yoga formed in the chart.
    """
    name: str
    planets: List[str] = Field(default_factory=list)
    strength: Optional[str] = None
    description: Optional[str] = None


class PlanetStrength(BaseModel):
    """
    Represents strength evaluation of a planet.
    """
    planet: str
    strength: str
    reasons: List[str] = Field(default_factory=list)


class HouseStrength(BaseModel):
    """
    Represents strength evaluation of a house.
    """
    house: int
    strength: str
    reasons: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Aggregated Derived Astrology
# ─────────────────────────────────────────────

class DerivedAstrology(BaseModel):
    """
    Represents all derived astrology from a kundali.
    """

    doshas: List[Dosha] = Field(default_factory=list)
    yogas: List[Yoga] = Field(default_factory=list)

    planet_strengths: Dict[str, PlanetStrength] = Field(default_factory=dict)
    house_strengths: Dict[int, HouseStrength] = Field(default_factory=dict)

    summary: Dict[str, str] = Field(
        default_factory=dict,
        description="High-level summaries by category (career, marriage, etc.)"
    )

    calculation_version: str
