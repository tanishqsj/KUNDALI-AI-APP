from typing import Dict

from app.domain.kundali.schemas import (
    KundaliChart,
    Ascendant,
    PlanetPosition,
)


# ─────────────────────────────────────────────
# DB → Domain
# ─────────────────────────────────────────────

def kundali_core_to_domain(
    ascendant_data: Dict,
    planets_data: Dict,
    houses_data: Dict,
    ayanamsa: str,
) -> KundaliChart:
    """
    Convert DB-stored kundali core JSON into domain KundaliChart.
    """

    ascendant = Ascendant(
        sign=ascendant_data["sign"],
        degree=ascendant_data["degree"],
        nakshatra=ascendant_data.get("nakshatra"),
    )

    planets = {}
    for name, pdata in planets_data.items():
        planets[name] = PlanetPosition(
            name=name,
            sign=pdata["sign"],
            degree=pdata["degree"],
            house=pdata["house"],
            nakshatra=pdata.get("nakshatra"),
            retrograde=pdata.get("retrograde", False),
        )

    # Ensure house keys are ints
    houses = {int(k): v for k, v in houses_data.items()}

    return KundaliChart(
        ascendant=ascendant,
        planets=planets,
        houses=houses,
        ayanamsa=ayanamsa,
    )


# ─────────────────────────────────────────────
# Domain → DB
# ─────────────────────────────────────────────

def kundali_core_to_persistence(
    kundali: KundaliChart,
) -> Dict[str, Dict]:
    """
    Convert domain KundaliChart into DB-storable JSON fields.
    """

    ascendant = {
        "sign": kundali.ascendant.sign,
        "degree": kundali.ascendant.degree,
        "nakshatra": kundali.ascendant.nakshatra,
    }

    planets = {}
    for name, planet in kundali.planets.items():
        planets[name] = {
            "sign": planet.sign,
            "degree": planet.degree,
            "house": planet.house,
            "nakshatra": planet.nakshatra,
            "retrograde": planet.retrograde,
        }

    houses = {str(k): v for k, v in kundali.houses.items()}

    return {
        "ascendant": ascendant,
        "planets": planets,
        "houses": houses,
    }
