from typing import Dict, List

from app.domain.kundali.schemas import KundaliChart
from app.domain.kundali.derived.schemas import HouseStrength


# Benefic and malefic planet classification (simplified)
BENEFIC_PLANETS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC_PLANETS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}


class HouseCalculator:
    """
    Calculates strength and influences of houses
    based on planetary placements.
    """

    def calculate(
        self,
        kundali: KundaliChart
    ) -> Dict[int, HouseStrength]:
        """
        Calculate strength for each house (1–12).
        """
        house_strengths: Dict[int, HouseStrength] = {}

        for house in range(1, 13):
            reasons: List[str] = []
            score = 0

            # Planets occupying this house
            occupying_planets = [
                p for p in kundali.planets.values()
                if p.house == house
            ]

            for planet in occupying_planets:
                if planet.name in BENEFIC_PLANETS:
                    score += 1
                    reasons.append(
                        f"{planet.name} (benefic) occupies house {house}"
                    )
                elif planet.name in MALEFIC_PLANETS:
                    score -= 1
                    reasons.append(
                        f"{planet.name} (malefic) occupies house {house}"
                    )

            # Normalize score to strength
            if score >= 2:
                strength = "strong"
            elif score <= -1:
                strength = "weak"
            else:
                strength = "average"

            house_strengths[house] = HouseStrength(
                house=house,
                strength=strength,
                reasons=reasons
            )

        return house_strengths
