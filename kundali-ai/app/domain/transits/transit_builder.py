from datetime import datetime
from typing import Tuple

from app.domain.kundali.schemas import KundaliChart
from app.domain.transits.schemas import TransitChart, Gochar
from app.domain.transits.transit_engine import TransitEngine
from app.domain.transits.gochar_calculator import GocharCalculator


class TransitBuilder:
    """
    Orchestrates transit and gochar calculation
    for a given kundali and timestamp.
    """

    def __init__(
        self,
        transit_engine: TransitEngine | None = None,
        gochar_calculator: GocharCalculator | None = None,
    ):
        self.transit_engine = transit_engine or TransitEngine()
        self.gochar_calculator = gochar_calculator or GocharCalculator()

    def build(
        self,
        kundali: KundaliChart,
        timestamp: datetime | None = None
    ) -> Tuple[TransitChart, Gochar]:
        """
        Build transit chart and gochar data.

        If timestamp is None, current UTC time is used.
        """

        if timestamp is None:
            timestamp = datetime.utcnow()

        # ─────────────────────────────────────────────
        # Transit chart
        # ─────────────────────────────────────────────

        transit_chart = self.transit_engine.calculate(timestamp)

        # ─────────────────────────────────────────────
        # Gochar
        # ─────────────────────────────────────────────

        gochar = self.gochar_calculator.calculate(
            kundali=kundali,
            transit=transit_chart
        )

        return transit_chart, gochar
