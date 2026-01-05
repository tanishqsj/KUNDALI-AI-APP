from typing import Dict

from app.domain.kundali.schemas import KundaliChart, Ascendant, PlanetPosition
from app.domain.kundali.divisional.base import BaseDivisionalCalculator

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

DASHAMSHA_SPAN = 30 / 10  # 3 degrees


class D10Calculator(BaseDivisionalCalculator):
    """
    Calculates the Dashamsha (D10) chart from a D1 kundali.
    Used primarily for career and professional analysis.
    """

    chart_type = "D10"
    calculation_version = "v1"

    def calculate(
        self,
        kundali: KundaliChart
    ):
        """
        Calculate the D10 chart.
        """

        # ─────────────────────────────────────────────
        # Ascendant (D10)
        # ─────────────────────────────────────────────

        d10_asc_sign, d10_asc_degree = self._dashamsha_position(
            kundali.ascendant.sign,
            kundali.ascendant.degree
        )

        ascendant = Ascendant(
            sign=d10_asc_sign,
            degree=d10_asc_degree,
            nakshatra=None,
        )

        # ─────────────────────────────────────────────
        # Planets (D10)
        # ─────────────────────────────────────────────

        planets: Dict[str, PlanetPosition] = {}

        for name, planet in kundali.planets.items():
            d10_sign, d10_degree = self._dashamsha_position(
                planet.sign,
                planet.degree
            )

            planets[name] = PlanetPosition(
                name=name,
                sign=d10_sign,
                degree=d10_degree,
                house=0,  # Houses optional for D10
                nakshatra=None,
                retrograde=planet.retrograde,
            )

        return self._build_chart(
            chart_type=self.chart_type,
            ascendant=ascendant,
            planets=planets,
        )

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def _dashamsha_position(
        self,
        sign: str,
        degree_in_sign: float
    ) -> tuple[str, float]:
        """
        Calculate Dashamsha sign and degree.
        """

        if sign not in SIGNS:
            raise ValueError(f"Invalid zodiac sign: {sign}")

        sign_index = SIGNS.index(sign)
        dashamsha_index = int(degree_in_sign // DASHAMSHA_SPAN)

        is_odd_sign = sign_index % 2 == 0  # Aries=0 → odd sign

        if is_odd_sign:
            d10_sign_index = (sign_index + dashamsha_index) % 12
        else:
            d10_sign_index = (sign_index - dashamsha_index) % 12

        d10_sign = SIGNS[d10_sign_index]

        degree_in_dashamsha = (degree_in_sign % DASHAMSHA_SPAN) * (30 / DASHAMSHA_SPAN)

        return d10_sign, round(degree_in_dashamsha, 2)
