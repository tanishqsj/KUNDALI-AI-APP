from typing import Dict
from pydantic import BaseModel

from app.domain.kundali.schemas import Ascendant, PlanetPosition


class DivisionalChart(BaseModel):
    """
    Represents a single divisional chart (D9, D10, etc.).
    """

    chart_type: str
    ascendant: Ascendant
    planets: Dict[str, PlanetPosition]
    calculation_version: str


class DivisionalCharts(BaseModel):
    """
    Container for all divisional charts of a kundali.
    """

    charts: Dict[str, DivisionalChart] = {}
    calculation_version: str = "v1"
