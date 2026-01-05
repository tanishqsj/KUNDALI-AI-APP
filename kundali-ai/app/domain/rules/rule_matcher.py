from typing import Any, Dict, Tuple

from app.domain.kundali.schemas import KundaliChart
from app.domain.kundali.derived.schemas import DerivedAstrology


class RuleMatcher:
    """
    Evaluates atomic rule conditions against domain objects.
    """

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def match(
        self,
        kundali: KundaliChart,
        derived: DerivedAstrology | None,
        condition: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a single atomic condition.

        Returns:
            (matched, trigger_snapshot)
        """
        entity = condition.get("entity")

        if entity == "planet":
            return self._match_planet(kundali, condition)

        if entity == "house":
            return self._match_house(derived, condition)

        if entity == "dosha":
            return self._match_dosha(derived, condition)

        # Unknown condition type
        return False, {}

    # ─────────────────────────────────────────────
    # Planet condition
    # ─────────────────────────────────────────────

    def _match_planet(
        self,
        kundali: KundaliChart,
        condition: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        planet_name = condition.get("name")
        required_house = condition.get("house")
        required_sign = condition.get("sign")

        planet = kundali.planets.get(planet_name)

        if not planet:
            return False, {}

        if required_house is not None and planet.house != required_house:
            return False, {}

        if required_sign is not None and planet.sign != required_sign:
            return False, {}

        return True, {
            "entity_type": "planet",
            "entity_key": planet_name,
            "snapshot": {
                "sign": planet.sign,
                "house": planet.house,
                "degree": planet.degree,
                "retrograde": planet.retrograde,
            },
        }

    # ─────────────────────────────────────────────
    # House condition
    # ─────────────────────────────────────────────

    def _match_house(
        self,
        derived: DerivedAstrology | None,
        condition: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        if not derived:
            return False, {}

        house_num = condition.get("house")
        required_strength = condition.get("strength")

        house_strength = derived.house_strengths.get(house_num)

        if not house_strength:
            return False, {}

        if required_strength and house_strength.strength != required_strength:
            return False, {}

        return True, {
            "entity_type": "house",
            "entity_key": str(house_num),
            "snapshot": {
                "strength": house_strength.strength,
                "reasons": house_strength.reasons,
            },
        }

    # ─────────────────────────────────────────────
    # Dosha condition
    # ─────────────────────────────────────────────

    def _match_dosha(
        self,
        derived: DerivedAstrology | None,
        condition: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        if not derived:
            return False, {}

        dosha_name = condition.get("name")
        required_present = condition.get("present", True)

        for dosha in derived.doshas:
            if dosha.name == dosha_name and dosha.present == required_present:
                return True, {
                    "entity_type": "dosha",
                    "entity_key": dosha_name,
                    "snapshot": {
                        "severity": dosha.severity,
                        "description": dosha.description,
                    },
                }

        return False, {}
