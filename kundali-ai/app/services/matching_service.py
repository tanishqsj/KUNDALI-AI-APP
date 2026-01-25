"""
Kundali Milan (Ashta Koot Matching) Service

Calculates compatibility score based on 8 factors (36 max points).
"""

from typing import Dict, Any, List
from app.domain.kundali.calculator import KundaliCalculator


class MatchingService:
    """
    Service to calculate Ashta Koot matching between two Kundalis.
    """

    # ─────────────────────────────────────────────
    # Constants / Lookup Tables
    # ─────────────────────────────────────────────

    VARNA_HIERARCHY = ["Shudra", "Vaishya", "Kshatriya", "Brahmin"]  # 0 = lowest

    # Vashya compatibility matrix (simplified)
    # Categories: Manava, Vanchar, Chatushpada, Jalchar, Keeta
    VASHYA_COMPAT = {
        ("Manava", "Manava"): 2,
        ("Manava", "Chatushpada"): 1,
        ("Chatushpada", "Chatushpada"): 2,
        ("Vanchar", "Vanchar"): 2,
        ("Jalchar", "Jalchar"): 2,
        ("Keeta", "Keeta"): 2,
    }

    # Yoni animal pairs - enemies/friends
    YONI_ENEMIES = {
        ("Horse", "Buffalo"), ("Elephant", "Lion"), ("Sheep", "Monkey"),
        ("Serpent", "Mongoose"), ("Dog", "Deer"), ("Cat", "Rat"),
        ("Tiger", "Cow"),
    }
    YONI_SAME = 4
    YONI_FRIENDLY = 3
    YONI_NEUTRAL = 2
    YONI_ENEMY = 0

    # Gana compatibility
    GANA_SCORES = {
        ("Deva", "Deva"): 6,
        ("Manushya", "Manushya"): 6,
        ("Rakshasa", "Rakshasa"): 6,
        ("Deva", "Manushya"): 5,
        ("Manushya", "Deva"): 5,
        ("Manushya", "Rakshasa"): 1,
        ("Rakshasa", "Manushya"): 1,
        ("Deva", "Rakshasa"): 0,
        ("Rakshasa", "Deva"): 0,
    }

    # Graha Maitri - Moon sign lords
    SIGN_LORDS = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
        "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
        "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
        "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
    }

    # Planet friendship table
    # 1 = Friend, 0 = Neutral, -1 = Enemy
    PLANET_FRIENDSHIP = {
        "Sun": {"Moon": 1, "Mars": 1, "Jupiter": 1, "Venus": -1, "Saturn": -1, "Mercury": 0},
        "Moon": {"Sun": 1, "Mercury": 1, "Mars": 0, "Jupiter": 0, "Venus": 0, "Saturn": 0},
        "Mars": {"Sun": 1, "Moon": 1, "Jupiter": 1, "Venus": 0, "Saturn": 0, "Mercury": -1},
        "Mercury": {"Sun": 1, "Venus": 1, "Moon": -1, "Mars": 0, "Jupiter": 0, "Saturn": 0},
        "Jupiter": {"Sun": 1, "Moon": 1, "Mars": 1, "Venus": -1, "Saturn": 0, "Mercury": -1},
        "Venus": {"Mercury": 1, "Saturn": 1, "Sun": -1, "Moon": -1, "Mars": 0, "Jupiter": 0},
        "Saturn": {"Mercury": 1, "Venus": 1, "Sun": -1, "Moon": -1, "Mars": -1, "Jupiter": 0},
    }

    # Bhakoot bad combinations (house distances)
    BHAKOOT_BAD = [(2, 12), (5, 9), (6, 8)]

    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]

    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
        "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
        "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]

    def __init__(self):
        self.calculator = KundaliCalculator()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def calculate_ashta_koot(
        self,
        boy_moon_sign: str,
        boy_moon_degree: float,
        girl_moon_sign: str,
        girl_moon_degree: float,
    ) -> Dict[str, Any]:
        """
        Calculate Ashta Koot matching score.

        Args:
            boy_moon_sign: Boy's Moon sign (e.g., "Aries")
            boy_moon_degree: Boy's Moon degree within sign (0-30)
            girl_moon_sign: Girl's Moon sign
            girl_moon_degree: Girl's Moon degree within sign

        Returns:
            Dict with total_score, max_score, verdict, and per-factor breakdown.
        """
        # Get Avakahada for both
        boy_ava = self.calculator.calculate_avakahada_chakra(boy_moon_sign, boy_moon_degree)
        girl_ava = self.calculator.calculate_avakahada_chakra(girl_moon_sign, girl_moon_degree)

        factors = []

        # 1. Varna (1 point)
        varna_score, varna_desc = self._calc_varna(boy_ava["Varna"], girl_ava["Varna"])
        factors.append({
            "name": "Varna", "score": varna_score, "max": 1, "description": varna_desc,
            "boy_value": boy_ava["Varna"], "girl_value": girl_ava["Varna"], "area": "Work & Status"
        })

        # 2. Vashya (2 points)
        vashya_score, vashya_desc = self._calc_vashya(boy_ava["Vashya"], girl_ava["Vashya"])
        factors.append({
            "name": "Vashya", "score": vashya_score, "max": 2, "description": vashya_desc,
            "boy_value": boy_ava["Vashya"], "girl_value": girl_ava["Vashya"], "area": "Dominance & Control"
        })

        # 3. Tara (3 points)
        tara_score, tara_desc = self._calc_tara(boy_ava["Nakshatra"], girl_ava["Nakshatra"])
        factors.append({
            "name": "Tara", "score": tara_score, "max": 3, "description": tara_desc,
            "boy_value": boy_ava["Nakshatra"].split(" (")[0], "girl_value": girl_ava["Nakshatra"].split(" (")[0], "area": "Destiny & Health"
        })

        # 4. Yoni (4 points)
        yoni_score, yoni_desc = self._calc_yoni(boy_ava["Yoni"], girl_ava["Yoni"])
        factors.append({
            "name": "Yoni", "score": yoni_score, "max": 4, "description": yoni_desc,
            "boy_value": boy_ava["Yoni"], "girl_value": girl_ava["Yoni"], "area": "Physical & Intimacy"
        })

        # 5. Graha Maitri (5 points)
        maitri_score, maitri_desc = self._calc_graha_maitri(boy_moon_sign, girl_moon_sign)
        boy_lord = self.SIGN_LORDS.get(boy_moon_sign, "Unknown")
        girl_lord = self.SIGN_LORDS.get(girl_moon_sign, "Unknown")
        factors.append({
            "name": "Graha Maitri", "score": maitri_score, "max": 5, "description": maitri_desc,
            "boy_value": boy_lord, "girl_value": girl_lord, "area": "Mental Compatibility"
        })

        # 6. Gana (6 points)
        gana_score, gana_desc = self._calc_gana(boy_ava["Gana"], girl_ava["Gana"])
        factors.append({
            "name": "Gana", "score": gana_score, "max": 6, "description": gana_desc,
            "boy_value": boy_ava["Gana"], "girl_value": girl_ava["Gana"], "area": "Temperament & Nature"
        })

        # 7. Bhakoot (7 points)
        bhakoot_score, bhakoot_desc = self._calc_bhakoot(boy_moon_sign, girl_moon_sign)
        factors.append({
            "name": "Bhakoot", "score": bhakoot_score, "max": 7, "description": bhakoot_desc,
            "boy_value": boy_moon_sign, "girl_value": girl_moon_sign, "area": "Love & Prosperity"
        })

        # 8. Nadi (8 points)
        nadi_score, nadi_desc = self._calc_nadi(boy_ava["Nadi"], girl_ava["Nadi"])
        factors.append({
            "name": "Nadi", "score": nadi_score, "max": 8, "description": nadi_desc,
            "boy_value": boy_ava["Nadi"], "girl_value": girl_ava["Nadi"], "area": "Health & Progeny"
        })

        total = sum(f["score"] for f in factors)
        max_total = 36

        # Verdict
        if total >= 25:
            verdict = "Excellent Match"
        elif total >= 18:
            verdict = "Good Match"
        elif total >= 12:
            verdict = "Average Match"
        else:
            verdict = "Below Average"

        return {
            "total_score": total,
            "max_score": max_total,
            "percentage": round((total / max_total) * 100, 1),
            "verdict": verdict,
            "factors": factors,
            "boy_details": boy_ava,
            "girl_details": girl_ava,
        }

    # ─────────────────────────────────────────────
    # Per-Factor Calculations
    # ─────────────────────────────────────────────

    def _calc_varna(self, boy_varna: str, girl_varna: str):
        """Varna: Boy's Varna >= Girl's Varna = 1 point."""
        boy_rank = self.VARNA_HIERARCHY.index(boy_varna) if boy_varna in self.VARNA_HIERARCHY else 0
        girl_rank = self.VARNA_HIERARCHY.index(girl_varna) if girl_varna in self.VARNA_HIERARCHY else 0

        if boy_rank >= girl_rank:
            return 1, f"Boy ({boy_varna}) is equal or higher than Girl ({girl_varna})."
        return 0, f"Boy ({boy_varna}) is lower than Girl ({girl_varna})."

    def _calc_vashya(self, boy_vashya: str, girl_vashya: str):
        """Vashya: Compatibility of influence types."""
        key = (boy_vashya, girl_vashya)
        rev_key = (girl_vashya, boy_vashya)

        if key in self.VASHYA_COMPAT:
            score = self.VASHYA_COMPAT[key]
        elif rev_key in self.VASHYA_COMPAT:
            score = self.VASHYA_COMPAT[rev_key]
        elif boy_vashya == girl_vashya:
            score = 2
        else:
            score = 0

        return score, f"Boy: {boy_vashya}, Girl: {girl_vashya}."

    def _calc_tara(self, boy_nak: str, girl_nak: str):
        """Tara: Based on Nakshatra distance."""
        # Extract base nakshatra name (remove pada)
        boy_base = boy_nak.split(" (")[0] if " (" in boy_nak else boy_nak
        girl_base = girl_nak.split(" (")[0] if " (" in girl_nak else girl_nak

        if boy_base not in self.NAKSHATRAS or girl_base not in self.NAKSHATRAS:
            return 1.5, "Could not determine Nakshatra indices."

        boy_idx = self.NAKSHATRAS.index(boy_base)
        girl_idx = self.NAKSHATRAS.index(girl_base)

        # Distance from girl to boy (count boy from girl's nakshatra)
        dist = (boy_idx - girl_idx) % 27 + 1
        tara_num = ((dist - 1) % 9) + 1  # 1-9 cycle

        # Taras 3, 5, 7 are auspicious
        if tara_num in [3, 5, 7]:
            return 3, f"Tara {tara_num} is auspicious."
        elif tara_num in [1, 2, 4, 6, 8]:
            return 1.5, f"Tara {tara_num} is neutral."
        else:
            return 0, f"Tara {tara_num} is inauspicious."

    def _calc_yoni(self, boy_yoni: str, girl_yoni: str):
        """Yoni: Animal compatibility."""
        if boy_yoni == girl_yoni:
            return 4, f"Same Yoni ({boy_yoni}) — excellent physical compatibility."

        pair = (boy_yoni, girl_yoni)
        rev_pair = (girl_yoni, boy_yoni)

        if pair in self.YONI_ENEMIES or rev_pair in self.YONI_ENEMIES:
            return 0, f"{boy_yoni} and {girl_yoni} are enemies."

        # Simplified: not same, not enemy = neutral
        return 2, f"{boy_yoni} and {girl_yoni} are neutral."

    def _calc_graha_maitri(self, boy_sign: str, girl_sign: str):
        """Graha Maitri: Friendship between Moon sign lords."""
        boy_lord = self.SIGN_LORDS.get(boy_sign, "Unknown")
        girl_lord = self.SIGN_LORDS.get(girl_sign, "Unknown")

        if boy_lord == "Unknown" or girl_lord == "Unknown":
            return 2.5, "Could not determine lords."

        if boy_lord == girl_lord:
            return 5, f"Same lord ({boy_lord}) — excellent mental compatibility."

        friendship = self.PLANET_FRIENDSHIP.get(boy_lord, {}).get(girl_lord, 0)
        rev_friendship = self.PLANET_FRIENDSHIP.get(girl_lord, {}).get(boy_lord, 0)

        avg = (friendship + rev_friendship) / 2

        if avg >= 0.5:
            return 5, f"{boy_lord} and {girl_lord} are friends."
        elif avg >= 0:
            return 3, f"{boy_lord} and {girl_lord} are neutral."
        else:
            return 0, f"{boy_lord} and {girl_lord} are enemies."

    def _calc_gana(self, boy_gana: str, girl_gana: str):
        """Gana: Temperament matching."""
        key = (boy_gana, girl_gana)
        score = self.GANA_SCORES.get(key, 3)  # Default neutral

        return score, f"Boy: {boy_gana}, Girl: {girl_gana}."

    def _calc_bhakoot(self, boy_sign: str, girl_sign: str):
        """Bhakoot: Moon sign position check."""
        if boy_sign not in self.SIGNS or girl_sign not in self.SIGNS:
            return 3.5, "Could not determine sign indices."

        boy_idx = self.SIGNS.index(boy_sign)
        girl_idx = self.SIGNS.index(girl_sign)

        dist1 = (boy_idx - girl_idx) % 12 + 1
        dist2 = (girl_idx - boy_idx) % 12 + 1

        for bad in self.BHAKOOT_BAD:
            if (dist1, dist2) == bad or (dist2, dist1) == bad:
                return 0, f"Distance {dist1}/{dist2} indicates Bhakoot Dosha."

        return 7, f"No Bhakoot Dosha detected (distance: {dist1}/{dist2})."

    def _calc_nadi(self, boy_nadi: str, girl_nadi: str):
        """Nadi: Genetic compatibility (most critical)."""
        if boy_nadi == girl_nadi:
            return 0, f"Same Nadi ({boy_nadi}) — Nadi Dosha! Risk to progeny."
        return 8, f"Different Nadis ({boy_nadi} vs {girl_nadi}) — no Nadi Dosha."
