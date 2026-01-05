from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Core Atomic Schemas
# ─────────────────────────────────────────────

class PlanetPosition(BaseModel):
    """
    Represents a single planet's position in a chart.
    """
    name: str
    sign: str
    degree: float
    house: int
    nakshatra: Optional[str] = None
    retrograde: bool = False


class Ascendant(BaseModel):
    """
    Represents the ascendant (Lagna).
    """
    sign: str
    degree: float
    nakshatra: Optional[str] = None


# ─────────────────────────────────────────────
# Core Kundali Schema (D1)
# ─────────────────────────────────────────────

class KundaliChart(BaseModel):
    """
    Represents the core D1 (Rashi) kundali.
    """
    ascendant: Ascendant
    planets: Dict[str, PlanetPosition]
    houses: Dict[int, str]
    ayanamsa: str


# ─────────────────────────────────────────────
# Derived Astrology Schemas
# ─────────────────────────────────────────────

class Dosha(BaseModel):
    """
    Represents a detected dosha.
    """
    name: str
    present: bool
    description: Optional[str] = None


class Yoga(BaseModel):
    """
    Represents a detected yoga.
    """
    name: str
    planets: List[str]
    description: Optional[str] = None


class DerivedAstrology(BaseModel):
    """
    Represents derived astrological facts from a kundali.
    """
    doshas: List[Dosha] = Field(default_factory=list)
    yogas: List[Yoga] = Field(default_factory=list)
    planet_strengths: Dict[str, str] = Field(default_factory=dict)
    house_strengths: Dict[str, str] = Field(default_factory=dict)
    summary: Dict[str, str] = Field(default_factory=dict)


# ─────────────────────────────────────────────
# Divisional Charts
# ─────────────────────────────────────────────

class DivisionalChart(BaseModel):
    """
    Represents a divisional chart (D9, D10, etc.).
    """
    chart_type: str
    ascendant: Ascendant
    planets: Dict[str, PlanetPosition]


# ─────────────────────────────────────────────
# Transit & Gochar Schemas
# ─────────────────────────────────────────────

class TransitPlanet(BaseModel):
    """
    Represents a planet's transit position.
    """
    sign: str
    degree: float
    retrograde: bool


class TransitChart(BaseModel):
    """
    Represents planetary transits for a specific date.
    """
    date: str
    planets: Dict[str, TransitPlanet]


class Gochar(BaseModel):
    """
    Represents gochar (relative transits).
    """
    from_lagna: Dict[str, int]
    from_moon: Dict[str, int]
