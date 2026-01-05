from abc import ABC, abstractmethod
from typing import Dict

from app.domain.kundali.schemas import KundaliChart, Ascendant, PlanetPosition
from app.domain.kundali.divisional.schemas import DivisionalChart


class BaseDivisionalCalculator(ABC):
    """
    Abstract base class for all divisional chart calculators.

    Each divisional chart (D9, D10, etc.) must:
    - Implement `chart_type`
    - Implement `calculate`
    """

    chart_type: str
    calculation_version: str = "v1"

    @abstractmethod
    def calculate(
        self,
        kundali: KundaliChart
    ) -> DivisionalChart:
        """
        Calculate the divisional chart from a D1 kundali.
        """
        raise NotImplementedError

    # ─────────────────────────────────────────────
    # Shared helpers
    # ─────────────────────────────────────────────

    def _build_chart(
        self,
        chart_type: str,
        ascendant: Ascendant,
        planets: Dict[str, PlanetPosition],
    ) -> DivisionalChart:
        """
        Helper to assemble a DivisionalChart object.
        """
        return DivisionalChart(
            chart_type=chart_type,
            ascendant=ascendant,
            planets=planets,
            calculation_version=self.calculation_version,
        )
