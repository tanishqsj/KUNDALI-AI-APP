from dataclasses import dataclass
from datetime import date, time

from app.domain.kundali.schemas import (
    KundaliChart,
    Ascendant,
    PlanetPosition,
)
from app.domain.kundali.calculator import KundaliCalculator


@dataclass(frozen=True)
class BirthInput:
    """
    Immutable birth input used for kundali calculation.
    """
    birth_date: date
    birth_time: time
    latitude: float
    longitude: float
    timezone: str
    ayanamsa: str = "Lahiri"


class KundaliEngine:
    """
    Orchestrates kundali calculation.

    This class:
    - Accepts birth inputs
    - Delegates calculation to calculator
    - Returns domain KundaliChart
    """

    def __init__(self, calculator: KundaliCalculator):
        self.calculator = calculator

    def generate(self, birth: BirthInput) -> KundaliChart:
        """
        Generate the core D1 kundali chart.

        This method is:
        - Pure
        - Deterministic
        - Side-effect free
        """

        # ─────────────────────────────────────────────
        # Step 1: Raw astronomical calculation
        # ─────────────────────────────────────────────

        raw_result = self.calculator.calculate(
            birth_date=birth.birth_date,
            birth_time=birth.birth_time,
            latitude=birth.latitude,
            longitude=birth.longitude,
            timezone=birth.timezone,
            ayanamsa=birth.ayanamsa,
        )

        # ─────────────────────────────────────────────
        # Step 2: Build Ascendant
        # ─────────────────────────────────────────────

        asc = Ascendant(
            sign=raw_result["ascendant"]["sign"],
            degree=raw_result["ascendant"]["degree"],
            nakshatra=raw_result["ascendant"].get("nakshatra"),
        )

        # ─────────────────────────────────────────────
        # Step 3: Build Planet Positions
        # ─────────────────────────────────────────────

        planets = {}
        for name, data in raw_result["planets"].items():
            planets[name] = PlanetPosition(
                name=name,
                sign=data["sign"],
                degree=data["degree"],
                house=data["house"],
                nakshatra=data.get("nakshatra"),
                retrograde=data.get("retrograde", False),
            )

        # ─────────────────────────────────────────────
        # Step 4: Assemble Kundali Chart
        # ─────────────────────────────────────────────

        return KundaliChart(
            ascendant=asc,
            planets=planets,
            houses=raw_result["houses"],
            ayanamsa=birth.ayanamsa,
        )
