from typing import Dict, List, Any

from app.domain.kundali.schemas import KundaliChart
from app.persistence.models.rule import Rule


class RuleMatchResult:
    """
    Represents a successful rule match with explanation data.
    """

    def __init__(
        self,
        rule: Rule,
        matched: bool,
        triggered_entities: List[Dict[str, Any]],
    ):
        self.rule = rule
        self.matched = matched
        self.triggered_entities = triggered_entities


class RuleEngine:
    """
    Evaluates astrology rules against a kundali chart.

    This engine:
    - Evaluates structured rule conditions
    - Is deterministic
    - Produces explainable outputs
    """

    def evaluate(
        self,
        kundali: KundaliChart,
        rules: List[Rule],
    ) -> List[RuleMatchResult]:
        """
        Evaluate all rules against a kundali chart.
        """
        results: List[RuleMatchResult] = []

        for rule in rules:
            matched, triggers = self._evaluate_rule(
                kundali,
                rule.conditions,
            )

            if matched:
                results.append(
                    RuleMatchResult(
                        rule=rule,
                        matched=True,
                        triggered_entities=triggers,
                    )
                )

        return results

    # ─────────────────────────────────────────────
    # Internal evaluation logic
    # ─────────────────────────────────────────────

    def _evaluate_rule(
        self,
        kundali: KundaliChart,
        conditions: Dict[str, Any],
    ) -> tuple[bool, List[Dict[str, Any]]]:
        """
        Evaluate a single rule condition tree.
        """
        if "all" in conditions:
            return self._evaluate_all(kundali, conditions["all"])

        if "any" in conditions:
            return self._evaluate_any(kundali, conditions["any"])

        # Unknown structure → fail safely
        return False, []

    def _evaluate_all(
        self,
        kundali: KundaliChart,
        clauses: List[Dict[str, Any]],
    ) -> tuple[bool, List[Dict[str, Any]]]:
        triggers = []

        for clause in clauses:
            ok, trigger = self._evaluate_clause(kundali, clause)
            if not ok:
                return False, []
            triggers.append(trigger)

        return True, triggers

    def _evaluate_any(
        self,
        kundali: KundaliChart,
        clauses: List[Dict[str, Any]],
    ) -> tuple[bool, List[Dict[str, Any]]]:
        for clause in clauses:
            ok, trigger = self._evaluate_clause(kundali, clause)
            if ok:
                return True, [trigger]

        return False, []

    # ─────────────────────────────────────────────
    # Clause evaluation
    # ─────────────────────────────────────────────

    def _evaluate_clause(
        self,
        kundali: KundaliChart,
        clause: Dict[str, Any],
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Evaluate a single atomic condition.

        Example clause:
        {
          "entity": "planet",
          "name": "Jupiter",
          "house": 10
        }
        """

        entity = clause.get("entity")

        if entity == "planet":
            return self._evaluate_planet_clause(kundali, clause)

        # Unsupported entity
        return False, {}

    def _evaluate_planet_clause(
        self,
        kundali: KundaliChart,
        clause: Dict[str, Any],
    ) -> tuple[bool, Dict[str, Any]]:
        planet_name = clause.get("name")
        required_house = clause.get("house")
        required_sign = clause.get("sign")

        planet = kundali.planets.get(planet_name)

        if not planet:
            return False, {}

        if required_house is not None and planet.house != required_house:
            return False, {}

        if required_sign is not None and planet.sign != required_sign:
            return False, {}

        # Clause matched → return trigger snapshot
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
