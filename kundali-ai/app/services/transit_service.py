from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from app.cache.transit_cache import TransitCache
from app.domain.transits.transit_builder import TransitBuilder


class TransitService:
    """
    Service wrapper around domain transit logic.

    Used by:
    - QueryRouter
    - ReportService
    """

    def __init__(self):
        self.builder = TransitBuilder()
        self.cache = TransitCache()

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def get_current(
        self,
        *,
        kundali_core_id: UUID,
        kundali_chart,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get current transit + gochar data for a kundali.
        """

        cached = await self.cache.get_transits(
        kundali_core_id=kundali_core_id,
        )

        if cached:
            return cached
        
        transit_chart, gochar = self.builder.build(
        kundali=kundali_chart,
        timestamp=timestamp,
        )

        result = {
            "transit": transit_chart.model_dump(),
            "gochar": gochar.model_dump(),
        }

        await self.cache.set_transits(
            kundali_core_id=kundali_core_id,
            data=result,
        )

        return result
