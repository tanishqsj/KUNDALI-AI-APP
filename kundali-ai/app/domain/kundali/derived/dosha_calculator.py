from typing import List

from app.domain.kundali.schemas import KundaliChart
from app.domain.kundali.derived.schemas import Dosha


# Houses considered for Mangal Dosha
MANGAL_DOSHA_HOUSES = {1, 4, 7, 8, 12}


class DoshaCalculator:
    """
    Detects major doshas in a kundali.

    Current support:
    - Mangal Dosha
    - Kaal Sarp Dosha (simplified)
    """

    def calculate(
        self,
        kundali: KundaliChart
    ) -> List[Dosha]:
        """
        Calculate all applicable doshas.
        """
        doshas: List[Dosha] = []

        doshas.append(self._calculate_mangal_dosha(kundali))
        doshas.append(self._calculate_kaal_sarp_dosha(kundali))

        return doshas

    # ─────────────────────────────────────────────
    # Mangal Dosha
    # ─────────────────────────────────────────────

    def _calculate_mangal_dosha(
        self,
        kundali: KundaliChart
    ) -> Dosha:
        """
        Mangal Dosha occurs if Mars is placed in
        certain houses from the ascendant.
        """
        mars = kundali.planets.get("Mars")

        if not mars:
            return Dosha(
                name="Mangal Dosha",
                present=False,
                description="Mars position unknown"
            )

        if mars.house in MANGAL_DOSHA_HOUSES:
            return Dosha(
                name="Mangal Dosha",
                present=True,
                severity="medium",
                description=(
                    f"Mars is placed in house {mars.house}, "
                    "which is considered a Manglik position."
                ),
            )

        return Dosha(
            name="Mangal Dosha",
            present=False,
            description="Mars is not in a Manglik position."
        )

    # ─────────────────────────────────────────────
    # Kaal Sarp Dosha (Simplified)
    # ─────────────────────────────────────────────

    def _calculate_kaal_sarp_dosha(
        self,
        kundali: KundaliChart
    ) -> Dosha:
        """
        Simplified Kaal Sarp Dosha detection.

        Occurs if all planets are placed between
        Rahu and Ketu in the zodiac.
        """

        rahu = kundali.planets.get("Rahu")
        ketu = kundali.planets.get("Ketu")

        if not rahu or not ketu:
            return Dosha(
                name="Kaal Sarp Dosha",
                present=False,
                description="Nodes unknown"
            )

        rahu_house = rahu.house
        ketu_house = ketu.house

        def is_between(house: int) -> bool:
            if rahu_house < ketu_house:
                return rahu_house < house < ketu_house
            return house > rahu_house or house < ketu_house

        for planet in kundali.planets.values():
            if planet.name in {"Rahu", "Ketu"}:
                continue
            if not is_between(planet.house):
                return Dosha(
                    name="Kaal Sarp Dosha",
                    present=False,
                    description="Planets are not hemmed between Rahu and Ketu."
                )

        return Dosha(
            name="Kaal Sarp Dosha",
            present=True,
            severity="high",
            description=(
                "All planets are positioned between Rahu and Ketu, "
                "indicating Kaal Sarp Dosha."
            ),
        )
