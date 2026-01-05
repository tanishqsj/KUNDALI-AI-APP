# Placeholder for kundali-ai/app/domain/transits/transit_engine.py
from datetime import datetime
from typing import Dict
try:
    import swisseph as swe
except ImportError:
    swe = None
    print("WARNING: pyswisseph not installed. Transit calculations will fail.")

from app.domain.transits.schemas import TransitChart, TransitPlanet


class TransitEngine:
    """
    Calculates planetary transits for a given datetime.

    This engine:
    - Is ephemeris-agnostic
    - Returns pure domain schemas
    """

    calculation_version = "v1"

    PLANET_MAPPING = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE,
    }

    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]

    def calculate(
        self,
        timestamp: datetime
    ) -> TransitChart:
        """
        Calculate transit chart for a given datetime.

        NOTE:
        - Current implementation is a deterministic stub
        - Swiss Ephemeris will replace internals later
        """

        planets: Dict[str, TransitPlanet] = {}

        if swe:
            # 1. Julian Day
            hour_decimal = timestamp.hour + timestamp.minute / 60.0 + timestamp.second / 3600.0
            jd = swe.julday(timestamp.year, timestamp.month, timestamp.day, hour_decimal)

            # 2. Set Sidereal Mode (Lahiri)
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

            # 3. Calculate Planets
            for name, pid in self.PLANET_MAPPING.items():
                res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
                lon = res[0][0]
                speed = res[0][3]
                sign_index = int(lon // 30)

                planets[name] = TransitPlanet(
                    name=name,
                    sign=self.SIGNS[sign_index],
                    degree=round(lon % 30, 2),
                    retrograde=speed < 0,
                )

            # 4. Calculate Ketu
            rahu = planets["Rahu"]
            rahu_total = self.SIGNS.index(rahu.sign) * 30 + rahu.degree
            ketu_total = (rahu_total + 180) % 360
            planets["Ketu"] = TransitPlanet(
                name="Ketu",
                sign=self.SIGNS[int(ketu_total // 30)],
                degree=round(ketu_total % 30, 2),
                retrograde=True,
            )

        return TransitChart(
            timestamp=timestamp.isoformat(),
            planets=planets,
            calculation_version=self.calculation_version,
        )
