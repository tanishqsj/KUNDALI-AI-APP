from typing import Dict, List

from app.domain.kundali.schemas import KundaliChart
from app.domain.kundali.divisional.schemas import DivisionalChart, DivisionalCharts
from app.domain.kundali.divisional.base import BaseDivisionalCalculator
from app.domain.kundali.divisional.d9 import D9Calculator
from app.domain.kundali.divisional.d10 import D10Calculator


class DivisionalBuilder:
    """
    Orchestrates the calculation of all divisional charts
    for a given kundali.
    """

    def __init__(
        self,
        calculators: List[BaseDivisionalCalculator] | None = None
    ):
        # Default supported divisionals
        self.calculators = calculators or [
            D9Calculator(),
            D10Calculator(),
        ]

    def build(
        self,
        kundali: KundaliChart
    ) -> DivisionalCharts:
        """
        Build all supported divisional charts.
        """

        charts: Dict[str, DivisionalChart] = {}

        for calculator in self.calculators:
            chart = calculator.calculate(kundali)
            charts[chart.chart_type] = chart

        return DivisionalCharts(
            charts=charts,
            calculation_version=self.calculators[0].calculation_version if self.calculators else "v1"
        )
