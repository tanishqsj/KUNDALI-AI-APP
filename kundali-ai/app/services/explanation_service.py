from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.rules.rule_engine import RuleMatchResult
from app.persistence.repositories.rule_mapping_repo import RuleMappingRepository
from app.persistence.repositories.rule_repo import RuleRepository


class ExplanationService:
    """
    Converts rule matches and their triggers into
    structured, deterministic explanations.
    """

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def build_explanations(
        self,
        session: AsyncSession,
        kundali_core_id: UUID,
        rule_results: List[RuleMatchResult],
        dashas: List[Dict[str, Any]] | None = None,
        sade_sati: Dict[str, Any] | None = None,
        dosha_analysis: Dict[str, Any] | None = None,
        avakahada: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        mapping_repo = RuleMappingRepository(session)
        rule_repo = RuleRepository(session)

        explanations: List[Dict[str, Any]] = []

        for result in rule_results:
            rule = await rule_repo.get_by_id(result.rule.id)
            mappings = await mapping_repo.list_for_rule_and_kundali(
                rule_id=result.rule.id,
                kundali_core_id=kundali_core_id,
            )

            explanations.append(
                self._build_single_explanation(
                    rule=rule,
                    mappings=mappings,
                    confidence=result.confidence,
                )
            )

        # --- Add Derived Explanations ---

        if sade_sati and sade_sati.get("status", "None") != "None":
            explanations.append(self._build_sade_sati_explanation(sade_sati))

        if dosha_analysis:
            for name, data in dosha_analysis.items():
                if data.get("present"):
                    explanations.append(self._build_dosha_explanation(name, data))

        if dashas:
            current = self._find_current_dasha(dashas)
            if current:
                explanations.append(self._build_dasha_explanation(current))

        if avakahada:
            explanations.append(self._build_avakahada_explanation(avakahada))

        return explanations

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    def _build_single_explanation(
        self,
        rule,
        mappings,
        confidence: str,
    ) -> Dict[str, Any]:
        triggers = [
            {
                "entity_type": m.entity_type,
                "entity_key": m.entity_key,
                "snapshot": m.entity_snapshot,
            }
            for m in mappings
        ]

        return {
            "rule_key": rule.rule_key,
            "category": rule.category,
            "impact": rule.effects.get("impact"),
            "confidence": confidence,
            "explanation": {
                "summary": self._human_summary(rule, triggers),
                "triggers": triggers,
            },
        }

    def _human_summary(
        self,
        rule,
        triggers: List[Dict[str, Any]],
    ) -> str:
        if not triggers:
            return f"Rule '**{rule.rule_key}**' matched."

        parts = []
        for t in triggers:
            if t["entity_type"] == "planet":
                parts.append(
                    f"**{t['entity_key']}** in **{t['snapshot'].get('sign')}** "
                    f"(house **{t['snapshot'].get('house')}**)"
                )
            elif t["entity_type"] == "house":
                parts.append(
                    f"house **{t['entity_key']}** is "
                    f"**{t['snapshot'].get('strength')}**"
                )
            elif t["entity_type"] == "dosha":
                parts.append(f"**{t['entity_key']}** dosha present")

        joined = "; ".join(parts)
        return f"This applies because {joined}."

    def _build_sade_sati_explanation(self, sade_sati: Dict[str, Any]) -> Dict[str, Any]:
        status = sade_sati.get("status", "Unknown")
        desc = sade_sati.get("description", "")
        return {
            "rule_key": "sade_sati",
            "category": "Transit",
            "impact": "High" if "Peak" in status else "Medium",
            "confidence": "1.0",
            "explanation": {
                "summary": f"Sade Sati Status: **{status}**. {desc}",
                "triggers": [],
            },
        }

    def _build_dosha_explanation(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        dosha_name = name.replace("_", " ").title() + " Dosha"
        return {
            "rule_key": f"dosha_{name}",
            "category": "Dosha",
            "impact": "High",
            "confidence": "1.0",
            "explanation": {
                "summary": f"**{dosha_name}** is present. {data.get('description', '')}",
                "triggers": [],
            },
        }

    def _build_dasha_explanation(self, current: Dict[str, Any]) -> Dict[str, Any]:
        md = current["mahadasha"]
        ad = current.get("antardasha")
        
        summary = f"Current Period: **{md['lord']}** Mahadasha"
        if ad:
            summary += f" / **{ad['lord']}** Antardasha"
            end_date = ad['end_date'].split('T')[0]
            summary += f" (until {end_date})."
        else:
            end_date = md['end_date'].split('T')[0]
            summary += f" (until {end_date})."

        return {
            "rule_key": "vimshottari_dasha",
            "category": "Timing",
            "impact": "High",
            "confidence": "1.0",
            "explanation": {
                "summary": summary,
                "triggers": [],
            },
        }

    def _build_avakahada_explanation(self, avakahada: Dict[str, Any]) -> Dict[str, Any]:
        details = ", ".join([f"**{k}**: {v}" for k, v in avakahada.items()])
        return {
            "rule_key": "avakahada_chakra",
            "category": "Profile",
            "impact": "Low",
            "confidence": "1.0",
            "explanation": {
                "summary": f"Birth Profile Attributes: {details}",
                "triggers": [],
            },
        }

    def _find_current_dasha(self, dashas: List[Dict[str, Any]]) -> Dict[str, Any] | None:
        now = datetime.utcnow().isoformat()
        for d in dashas:
            if d["start_date"] <= now <= d["end_date"]:
                result = {"mahadasha": d}
                if "antardashas" in d:
                    for ad in d["antardashas"]:
                        if ad["start_date"] <= now <= ad["end_date"]:
                            result["antardasha"] = ad
                            break
                return result
        return None
