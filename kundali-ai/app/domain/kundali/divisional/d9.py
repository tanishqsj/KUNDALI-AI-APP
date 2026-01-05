from typing import Dict

from app.domain.kundali.schemas import KundaliChart, Ascendant, PlanetPosition
from app.domain.kundali.divisional.base import BaseDivisionalCalculator

# Zodiac order
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAVAMSHA_SPAN = 30 / 9  # 3.333333...


class D9Calculator(BaseDivisionalCalculator):
    """
    Calculates the Navamsha (D9) chart from a D1 kundali.
    """

    chart_type = "D9"
    calculation_version = "v1"

    def calculate(
        self,
        kundali: KundaliChart
    ):
        """
        Calculate the D9 chart.
        """

        # ─────────────────────────────────────────────
        # Ascendant (D9)
        # ─────────────────────────────────────────────

        d9_asc_sign, d9_asc_degree = self._navamsha_position(
            kundali.ascendant.sign,
            kundali.ascendant.degree
        )

        ascendant = Ascendant(
            sign=d9_asc_sign,
            degree=d9_asc_degree,
            nakshatra=None,
        )

        # ─────────────────────────────────────────────
        # Planets (D9)
        # ─────────────────────────────────────────────

        planets: Dict[str, PlanetPosition] = {}

        for name, planet in kundali.planets.items():
            d9_sign, d9_degree = self._navamsha_position(
                planet.sign,
                planet.degree
            )

            planets[name] = PlanetPosition(
                name=name,
                sign=d9_sign,
                degree=d9_degree,
                house=0,  # Houses computed later if needed
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

    def _navamsha_position(
        self,
        sign: str,
        degree_in_sign: float
    ) -> tuple[str, float]:
        """
        Calculate Navamsha sign and degree.
        """
        if sign not in SIGNS:
            raise ValueError(f"Invalid zodiac sign: {sign}")

        sign_index = SIGNS.index(sign)

        # Which Navamsha within the sign (0–8)
        navamsha_index = int(degree_in_sign // NAVAMSHA_SPAN)

        # Navamsha sign progression
        d9_sign_index = (sign_index * 9 + navamsha_index) % 12
        d9_sign = SIGNS[d9_sign_index]

        # Degree within the Navamsha
        degree_in_navamsha = (degree_in_sign % NAVAMSHA_SPAN) * (30 / NAVAMSHA_SPAN)

        return d9_sign, round(degree_in_navamsha, 2)
