from typing import Dict

from app.domain.kundali.schemas import KundaliChart
from app.domain.transits.schemas import TransitChart, Gochar, GocharPlanet


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


class GocharCalculator:
    """
    Calculates gochar (relative transit positions)
    from Lagna and Moon.
    """

    calculation_version = "v1"

    def calculate(
        self,
        kundali: KundaliChart,
        transit: TransitChart
    ) -> Gochar:
        """
        Calculate gochar for all transit planets.
        """

        lagna_sign = kundali.ascendant.sign
        moon_sign = kundali.planets.get("Moon").sign if "Moon" in kundali.planets else None

        gochar_planets: Dict[str, GocharPlanet] = {}

        for planet_name, transit_planet in transit.planets.items():
            from_lagna = self._house_from_reference(
                lagna_sign,
                transit_planet.sign
            )

            from_moon = None
            if moon_sign:
                from_moon = self._house_from_reference(
                    moon_sign,
                    transit_planet.sign
                )

            gochar_planets[planet_name] = GocharPlanet(
                planet=planet_name,
                from_lagna_house=from_lagna,
                from_moon_house=from_moon,
            )

        return Gochar(
            planets=gochar_planets,
            calculation_version=self.calculation_version
        )

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def _house_from_reference(
        self,
        reference_sign: str,
        transit_sign: str
    ) -> int:
        """
        Calculate house number of transit_sign
        from reference_sign (Lagna or Moon).
        """
        if reference_sign not in SIGNS or transit_sign not in SIGNS:
            raise ValueError("Invalid zodiac sign for gochar calculation")

        ref_index = SIGNS.index(reference_sign)
        trans_index = SIGNS.index(transit_sign)

        # Inclusive forward count (1–12)
        return ((trans_index - ref_index) % 12) + 1
