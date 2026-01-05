from typing import Tuple

# Nakshatra names in order (Ashwini → Revati)
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_SPAN = 360 / 27  # 13.333333...


class NakshatraCalculator:
    """
    Utility to calculate nakshatra from sign + degree.
    """

    def calculate(
        self,
        sign: str,
        degree_in_sign: float
    ) -> Tuple[str, int]:
        """
        Calculate nakshatra name and pada.

        Returns:
            (nakshatra_name, pada_number)
        """

        if sign not in SIGN_ORDER:
            raise ValueError(f"Invalid zodiac sign: {sign}")

        # Convert sign + degree → absolute zodiac degree
        sign_index = SIGN_ORDER.index(sign)
        absolute_degree = (sign_index * 30) + degree_in_sign

        # Determine nakshatra index
        nakshatra_index = int(absolute_degree // NAKSHATRA_SPAN)
        nakshatra_name = NAKSHATRAS[nakshatra_index]

        # Determine pada (each nakshatra has 4 padas)
        degree_within_nakshatra = absolute_degree % NAKSHATRA_SPAN
        pada = int(degree_within_nakshatra // (NAKSHATRA_SPAN / 4)) + 1

        return nakshatra_name, pada
