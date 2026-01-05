from datetime import date, time, datetime, timedelta
from typing import Dict, List, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import math
try:
    import swisseph as swe
except ImportError:
    # Fallback or error if not installed, but we assume it is for this request
    swe = None
    print("WARNING: pyswisseph not installed. Calculations will fail.")


class KundaliCalculator:
    """
    Astronomical calculator for kundali generation.

    This class:
    - Converts birth inputs into planetary positions
    - Is engine-agnostic (Swiss Ephemeris / future engines)
    - Returns raw, structured data (no domain objects)
    """

    def __init__(self):
        # Set default ephemeris path if needed, or rely on built-in Moshier fallback
        # swe.set_ephe_path('/path/to/ephe') 
        # Default to Lahiri Ayanamsa
        if swe:
            swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def calculate(
        self,
        birth_date: date,
        birth_time: time,
        latitude: float,
        longitude: float,
        timezone: str,
        ayanamsa: str,
    ) -> Dict:
        """
        Calculate core astronomical data for kundali.

        Returns a normalized dict consumed by KundaliEngine.
        """

        # Set Ayanamsa mode
        if swe:
            if ayanamsa.lower() == "lahiri":
                swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
            else:
                swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0) # Default to Lahiri

        # Step 1: Convert to UTC datetime
        birth_dt_utc = self._to_utc_datetime(
            birth_date, birth_time, timezone
        )

        # Step 2: Julian Day
        julian_day = self._julian_day(birth_dt_utc)

        # Step 3: Calculate ascendant
        ascendant = self._calculate_ascendant(
            julian_day, latitude, longitude
        )

        # Step 4: Calculate planetary positions
        planets = self._calculate_planets(
            julian_day, latitude, longitude, ascendant["sign"]
        )

        # Step 5: Calculate houses
        houses = self._calculate_houses(ascendant["sign"])

        return {
            "ascendant": ascendant,
            "planets": planets,
            "houses": houses,
            "ayanamsa": round(swe.get_ayanamsa_ut(julian_day), 4) if swe else 0.0,
        }

    # ─────────────────────────────────────────────
    # Time & Astronomy Helpers
    # ─────────────────────────────────────────────

    def _to_utc_datetime(
        self,
        birth_date: date,
        birth_time: time,
        timezone: str,
    ) -> datetime:
        """
        Convert local birth date & time into UTC datetime.

        NOTE:
        - For now, timezone is assumed correct and fixed
        - In production, use zoneinfo / pytz
        """
        local_dt = datetime.combine(birth_date, birth_time)
        
        try:
            # Attach the provided timezone (e.g., "Asia/Kolkata")
            local_tz = ZoneInfo(timezone)
            local_dt_aware = local_dt.replace(tzinfo=local_tz)
            
            # Convert to UTC
            utc_dt = local_dt_aware.astimezone(ZoneInfo("UTC"))
            
            # Return naive UTC datetime (swisseph expects naive numbers)
            return utc_dt.replace(tzinfo=None)
            
        except (ZoneInfoNotFoundError, ValueError) as e:
            print(f"WARNING: Timezone '{timezone}' not found or invalid ({e}). Defaulting to UTC.")
            return local_dt

    def _julian_day(self, dt: datetime) -> float:
        """
        Calculate Julian Day from datetime.

        This is a simplified implementation.
        Swiss Ephemeris will replace this internally.
        """
        if swe:
            hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            return swe.julday(dt.year, dt.month, dt.day, hour_decimal)
        
        return 0.0 # Should not happen if swe is installed

    # ─────────────────────────────────────────────
    # Ascendant
    # ─────────────────────────────────────────────

    def _calculate_ascendant(
        self,
        julian_day: float,
        latitude: float,
        longitude: float,
    ) -> Dict:
        """
        Calculate ascendant sign and degree.

        NOTE:
        - This is a placeholder mathematical approximation
        - Swiss Ephemeris will replace this
        """
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]

        if swe:
            # swe.houses returns (cusps, ascmc)
            # ascmc[0] is Ascendant. Note: swe.houses is always Tropical.
            # We must subtract Ayanamsa to get Sidereal Ascendant.
            cusps, ascmc = swe.houses(julian_day, latitude, longitude, b'P')
            tropical_asc = ascmc[0]
            ayanamsa = swe.get_ayanamsa_ut(julian_day)
            sidereal_asc = (tropical_asc - ayanamsa) % 360
            
            degree = sidereal_asc
            sign_index = int(degree // 30)

        return {
            "sign": signs[sign_index],
            "degree": round(degree % 30, 2),
            "nakshatra": self._calculate_nakshatra(degree) if swe else None,
        }

    # ─────────────────────────────────────────────
    # Planets
    # ─────────────────────────────────────────────

    def _calculate_planets(
        self,
        julian_day: float,
        latitude: float,
        longitude: float,
        ascendant_sign: str,
    ) -> Dict[str, Dict]:
        """
        Calculate planetary positions.

        NOTE:
        - This is a STUB implementation
        - Structure is FINAL and will not change
        """

        planet_mapping = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE, # Mean Node is standard in Vedic
        }

        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]

        planets = {}
        asc_sign_index = signs.index(ascendant_sign)

        if swe:
            for name, pid in planet_mapping.items():
                # Calculate Sidereal position
                # FLG_SPEED allows us to check retrograde status
                res = swe.calc_ut(julian_day, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
                lon = res[0][0]
                speed = res[0][3]
                
                sign_index = int(lon // 30)
                # House relative to Ascendant (Whole Sign / Rashi Chart)
                house_num = (sign_index - asc_sign_index) % 12 + 1

                planets[name] = {
                    "sign": signs[sign_index],
                    "degree": round(lon % 30, 2),
                    "house": house_num,
                    "nakshatra": self._calculate_nakshatra(lon),
                    "retrograde": speed < 0,
                }

            # Calculate Ketu (180 degrees from Rahu)
            rahu_data = planets["Rahu"]
            rahu_total_deg = signs.index(rahu_data["sign"]) * 30 + rahu_data["degree"]
            ketu_total_deg = (rahu_total_deg + 180) % 360
            ketu_sign_index = int(ketu_total_deg // 30)
            planets["Ketu"] = {
                "sign": signs[ketu_sign_index],
                "degree": round(ketu_total_deg % 30, 2),
                "house": (ketu_sign_index - asc_sign_index) % 12 + 1,
                "nakshatra": self._calculate_nakshatra(ketu_total_deg),
                "retrograde": True, # Nodes are always retrograde (Mean)
            }

        return planets

    # ─────────────────────────────────────────────
    # Dasha Calculation (Vimshottari)
    # ─────────────────────────────────────────────

    def calculate_vimshottari_dasha(self, moon_degree: float, birth_date: date) -> List[Dict[str, Any]]:
        """
        Calculate Vimshottari Dasha sequence.
        """
        # 1. Constants
        # Order of Dasha Lords and their duration in years
        dasha_lords = [
            ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
            ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
        ]
        
        # Nakshatra span (360 / 27) = 13.3333... degrees
        nakshatra_span = 360.0 / 27.0
        
        # 2. Determine starting point
        # Normalize moon degree
        moon_lon = moon_degree % 360
        
        # Find Nakshatra Index (0-26)
        nakshatra_idx = int(moon_lon / nakshatra_span)
        
        # Degrees traversed in current Nakshatra
        traversed = moon_lon - (nakshatra_idx * nakshatra_span)
        
        # Fraction remaining (Balance)
        fraction_remaining = 1.0 - (traversed / nakshatra_span)
        
        # 3. Map Nakshatra to Dasha Lord
        # The cycle of 9 lords repeats. 
        # Ashwini (0) -> Ketu (0), Bharani (1) -> Venus (1), ...
        start_lord_idx = nakshatra_idx % 9
        start_lord_name, start_lord_years = dasha_lords[start_lord_idx]
        
        # 4. Calculate Balance of Dasha at Birth
        balance_years = start_lord_years * fraction_remaining
        
        # 5. Generate Sequence
        dashas = []
        current_date = birth_date
        
        # Helper to add years to date
        def add_years(d, years):
            try:
                return d.replace(year=d.year + int(years))
            except ValueError:
                # Handle leap year edge case (Feb 29 -> Feb 28)
                return d.replace(year=d.year + int(years), day=28)

        # First Dasha (Balance)
        # Approximate end date for the balance
        # For simplicity in this view, we treat balance as full years/fraction logic roughly
        # A robust implementation would handle days/months. Here we project the end date.
        days_remaining = balance_years * 365.25
        end_date = current_date + timedelta(days=days_remaining)
        
        # Calculate Antardashas for the first (balance) Mahadasha
        # Note: For the balance dasha, we technically enter in the middle of an Antardasha.
        # For simplicity in this version, we will generate the full Antardasha sequence 
        # for the Lord but mark the start date correctly, or just list them.
        # A precise balance calculation for Antardasha is complex; 
        # here we generate the standard sequence for the Lord.
        antardashas_balance = self._calculate_antardashas(
            mahadasha_lord=start_lord_name,
            mahadasha_years=start_lord_years,
            start_date=current_date, # This is approximate for balance
            is_balance=True
        )

        dashas.append({
            "lord": start_lord_name,
            "start_date": current_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_years": round(balance_years, 2),
            "antardashas": antardashas_balance
        })
        
        current_date = end_date
        
        # Next Dashas (Full cycles)
        # We'll generate a few cycles (e.g., up to 120 years of life)
        for i in range(1, 10):
            idx = (start_lord_idx + i) % 9
            lord_name, duration = dasha_lords[idx]
            
            end_date = add_years(current_date, duration)
            
            # Calculate Antardashas
            antardashas = self._calculate_antardashas(
                mahadasha_lord=lord_name,
                mahadasha_years=duration,
                start_date=current_date
            )
            
            dashas.append({
                "lord": lord_name,
                "start_date": current_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_years": duration,
                "antardashas": antardashas
            })
            
            current_date = end_date
            
        return dashas

    def _calculate_antardashas(
        self, 
        mahadasha_lord: str, 
        mahadasha_years: int, 
        start_date: date,
        is_balance: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Calculate Antardasha (sub-periods) for a given Mahadasha.
        """
        dasha_lords = [
            ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
            ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
        ]
        
        # Find start index (Antardasha starts with the Mahadasha lord)
        start_idx = next(i for i, v in enumerate(dasha_lords) if v[0] == mahadasha_lord)
        
        sub_periods = []
        current = start_date
        
        for i in range(9):
            idx = (start_idx + i) % 9
            sub_lord, sub_years = dasha_lords[idx]
            
            # Formula: (Mahadasha Years * Antardasha Years) / 120 = Years duration
            duration_years = (mahadasha_years * sub_years) / 120.0
            days = duration_years * 365.25
            
            end = current + timedelta(days=days)
            
            sub_periods.append({
                "lord": sub_lord,
                "start_date": current.isoformat(),
                "end_date": end.isoformat(),
                "duration_months": round(duration_years * 12, 2)
            })
            current = end
            
        return sub_periods

    # ─────────────────────────────────────────────
    # Sade Sati Calculation
    # ─────────────────────────────────────────────

    def calculate_sade_sati(self, natal_moon_sign: str, check_date: date) -> Dict[str, Any]:
        """
        Calculate current Sade Sati status based on Saturn's transit.
        """
        if not swe:
            return {"status": "Unknown", "description": "Ephemeris not available"}

        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]

        # 1. Get Saturn's current position
        # Convert check_date to Julian Day
        hour_decimal = 12.0 # Noon
        jd = swe.julday(check_date.year, check_date.month, check_date.day, hour_decimal)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        
        res = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
        saturn_lon = res[0][0]
        saturn_sign_index = int(saturn_lon // 30)
        
        moon_sign_index = signs.index(natal_moon_sign)
        
        # 2. Calculate relative position (Saturn - Moon)
        # We want the house position of Saturn relative to Moon (1st house = 0 diff)
        diff = (saturn_sign_index - moon_sign_index) % 12
        
        status = "None"
        desc = "Saturn is not in a critical position relative to your Moon."
        
        if diff == 11: # 12th House
            status = "Sade Sati (Rising)"
            desc = "Saturn is in the 12th house from your Moon. This is the first phase of Sade Sati."
        elif diff == 0: # 1st House
            status = "Sade Sati (Peak)"
            desc = "Saturn is transiting over your natal Moon. This is the peak phase of Sade Sati."
        elif diff == 1: # 2nd House
            status = "Sade Sati (Setting)"
            desc = "Saturn is in the 2nd house from your Moon. This is the final phase of Sade Sati."
        elif diff == 3: # 4th House
            status = "Dhaiya (Small Panoti)"
            desc = "Saturn is in the 4th house from your Moon (Ardha-Ashtama Shani)."
        elif diff == 7: # 8th House
            status = "Dhaiya (Small Panoti)"
            desc = "Saturn is in the 8th house from your Moon (Ashtama Shani)."
            
        return {
            "status": status,
            "description": desc,
            "saturn_sign": signs[saturn_sign_index],
            "moon_sign": natal_moon_sign
        }

    # ─────────────────────────────────────────────
    # Dosha Calculations
    # ─────────────────────────────────────────────

    def calculate_mangal_dosha(self, planets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for Mangal Dosha (Mars in 1, 2, 4, 7, 8, 12).
        """
        if "Mars" not in planets:
            return {"present": False, "description": "Mars position unknown"}
            
        mars = planets["Mars"]
        # Handle Pydantic model or dict
        house = getattr(mars, "house", None)
        if house is None and isinstance(mars, dict):
             house = mars.get("house")

        is_dosha = house in [1, 2, 4, 7, 8, 12]
        
        return {
            "present": is_dosha,
            "description": f"Mars is in House {house}." + (" This indicates Mangal Dosha." if is_dosha else " No Mangal Dosha detected.")
        }

    def calculate_kalsarpa_dosha(self, planets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for Kalsarpa Yoga/Dosha (All planets hemmed between Rahu and Ketu).
        """
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]
        
        def get_abs_degree(p):
            sign_name = getattr(p, "sign", None) or p.get("sign")
            deg = getattr(p, "degree", None) or p.get("degree")
            if sign_name not in signs: return 0
            return signs.index(sign_name) * 30 + deg

        if "Rahu" not in planets or "Ketu" not in planets:
             return {"present": False, "description": "Nodes unknown"}

        rahu_deg = get_abs_degree(planets["Rahu"]) % 360
        ketu_deg = get_abs_degree(planets["Ketu"]) % 360
        
        others = []
        for name, p in planets.items():
            if name not in ["Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]:
                others.append(get_abs_degree(p) % 360)
        
        if not others:
             return {"present": False, "description": "No other planets found"}

        # Check Arc 1 (Rahu -> Ketu counter-clockwise)
        # If Rahu < Ketu: range is [Rahu, Ketu]
        # If Rahu > Ketu: range is [Rahu, 360] U [0, Ketu]
        def in_arc(deg, start, end):
            if start < end:
                return start <= deg <= end
            else:
                return deg >= start or deg <= end

        # Check if all planets are in the arc from Rahu to Ketu
        all_in_rahu_ketu = all(in_arc(d, rahu_deg, ketu_deg) for d in others)
        
        # Check if all planets are in the arc from Ketu to Rahu
        all_in_ketu_rahu = all(in_arc(d, ketu_deg, rahu_deg) for d in others)
        
        if all_in_rahu_ketu:
            return {"present": True, "type": "Anant (Rahu to Ketu)", "description": "All planets are hemmed between Rahu and Ketu."}
        elif all_in_ketu_rahu:
            return {"present": True, "type": "Kulat (Ketu to Rahu)", "description": "All planets are hemmed between Ketu and Rahu."}
            
        return {"present": False, "description": "Planets are not hemmed between the nodes."}

    # ─────────────────────────────────────────────
    # Avakahada Chakra
    # ─────────────────────────────────────────────

    def calculate_avakahada_chakra(self, moon_sign: str, moon_degree: float) -> Dict[str, str]:
        """
        Calculate Avakahada Chakra details based on Moon Sign and Nakshatra.
        """
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]
        
        if moon_sign not in signs:
            return {}

        # 1. Determine Absolute Longitude & Nakshatra Index
        sign_idx = signs.index(moon_sign)
        abs_degree = (sign_idx * 30) + moon_degree
        
        nakshatra_span = 360.0 / 27.0
        nakshatra_idx = int(abs_degree / nakshatra_span)
        
        # Nakshatra Names (0-26)
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
            "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
            "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
            "Uttara Bhadrapada", "Revati"
        ]
        nak_name = nakshatras[nakshatra_idx] if 0 <= nakshatra_idx < 27 else "Unknown"

        # 2. Varna (Based on Sign)
        varna_map = {
            "Cancer": "Brahmin", "Scorpio": "Brahmin", "Pisces": "Brahmin",
            "Aries": "Kshatriya", "Leo": "Kshatriya", "Sagittarius": "Kshatriya",
            "Taurus": "Vaishya", "Virgo": "Vaishya", "Capricorn": "Vaishya",
            "Gemini": "Shudra", "Libra": "Shudra", "Aquarius": "Shudra"
        }
        varna = varna_map.get(moon_sign, "Unknown")

        # 3. Vashya (Based on Sign)
        vashya_map = {
            "Aries": "Chatushpada", "Taurus": "Chatushpada", 
            "Gemini": "Manava", "Cancer": "Jalchar",
            "Leo": "Vanchar", "Virgo": "Manava",
            "Libra": "Manava", "Scorpio": "Keeta",
            "Sagittarius": "Manava", # Simplified
            "Capricorn": "Jalchar", # Simplified
            "Aquarius": "Manava", "Pisces": "Jalchar"
        }
        vashya = vashya_map.get(moon_sign, "Unknown")

        # 4. Yoni (Based on Nakshatra)
        yoni_list = [
            "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", # 0-5
            "Cat", "Sheep", "Cat", "Rat", "Rat", # 6-10
            "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", # 11-15
            "Deer", "Deer", "Dog", "Monkey", "Mongoose", # 16-20
            "Monkey", "Lion", "Horse", "Lion", # 21-24
            "Cow", "Elephant" # 25-26
        ]
        yoni = yoni_list[nakshatra_idx] if 0 <= nakshatra_idx < len(yoni_list) else "Unknown"

        # 5. Gana (Based on Nakshatra)
        gana_list = [
            "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", # 0-5
            "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", # 6-10
            "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", # 11-15
            "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", # 16-20
            "Deva", "Rakshasa", "Rakshasa", "Manushya", # 21-24
            "Manushya", "Deva" # 25-26
        ]
        gana = gana_list[nakshatra_idx] if 0 <= nakshatra_idx < len(gana_list) else "Unknown"

        # 6. Nadi (Based on Nakshatra)
        nadi_map = {
            0: "Adi", 5: "Adi", 6: "Adi", 11: "Adi", 12: "Adi", 17: "Adi", 18: "Adi", 23: "Adi", 24: "Adi",
            1: "Madhya", 4: "Madhya", 7: "Madhya", 10: "Madhya", 13: "Madhya", 16: "Madhya", 19: "Madhya", 22: "Madhya", 25: "Madhya",
            2: "Antya", 3: "Antya", 8: "Antya", 9: "Antya", 14: "Antya", 15: "Antya", 20: "Antya", 21: "Antya", 26: "Antya"
        }
        nadi = nadi_map.get(nakshatra_idx, "Unknown")

        return {
            "Varna": varna,
            "Vashya": vashya,
            "Yoni": yoni,
            "Gana": gana,
            "Nadi": nadi,
            "Nakshatra": nak_name,
            "Sign": moon_sign
        }

    # ─────────────────────────────────────────────
    # Nakshatra Helper
    # ─────────────────────────────────────────────

    def _calculate_nakshatra(self, degree: float) -> str:
        """
        Calculate Nakshatra and Pada from longitude (0-360).
        """
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
            "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
            "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
            "Uttara Bhadrapada", "Revati"
        ]
        
        # Each Nakshatra is 13 degrees 20 minutes = 13.3333... degrees
        nakshatra_span = 360.0 / 27.0
        
        normalized_degree = degree % 360
        index = int(normalized_degree / nakshatra_span)
        
        # Calculate Pada (Quarter)
        remaining_degree = normalized_degree - (index * nakshatra_span)
        pada_span = nakshatra_span / 4.0
        pada = int(remaining_degree / pada_span) + 1
        
        return f"{nakshatras[index]} ({pada})"

    # ─────────────────────────────────────────────
    # Houses
    # ─────────────────────────────────────────────

    def _calculate_houses(self, ascendant_sign: str) -> Dict[int, str]:
        """
        Calculate house-to-sign mapping from ascendant.
        """
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]

        start_index = signs.index(ascendant_sign)

        houses = {}
        for i in range(12):
            houses[i + 1] = signs[(start_index + i) % 12]

        return houses
