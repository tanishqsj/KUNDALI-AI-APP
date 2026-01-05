from typing import Dict, Optional
from pydantic import BaseModel, Field

from app.domain.kundali.schemas import PlanetPosition


# ─────────────────────────────────────────────
# Transit Schemas
# ─────────────────────────────────────────────

class TransitPlanet(BaseModel):
    """
    Represents a planet's transit position at a given time.
    """
    name: str
    sign: str
    degree: float
    retrograde: bool = False


class TransitChart(BaseModel):
    """
    Represents a full transit chart for a specific datetime.
    """
    timestamp: str
    planets: Dict[str, TransitPlanet]
    calculation_version: str


# ─────────────────────────────────────────────
# Gochar Schemas
# ─────────────────────────────────────────────

class GocharPlanet(BaseModel):
    """
    Represents a planet's gochar (relative position).
    """
    planet: str
    from_lagna_house: Optional[int] = None
    from_moon_house: Optional[int] = None


class Gochar(BaseModel):
    """
    Represents gochar interpretation base data.
    """
    planets: Dict[str, GocharPlanet]
    calculation_version: str = Field(
        default="v1",
        description="Version of gochar calculation logic"
    )
