import base64
from typing import Optional
from uuid import UUID

from app.cache.base import BaseCache
from app.cache.keys import CacheKeys
from app.cache.ttl import CacheTTL


class ReportCache(BaseCache):
    """
    Cache for generated PDF reports.

    Stores PDF bytes as base64-encoded strings.
    """

    async def get_report(
        self,
        *,
        kundali_core_id: UUID,
        include_transits: bool,
    ) -> Optional[bytes]:
        """
        Fetch cached PDF report.
        """
        key = CacheKeys.report(
            kundali_core_id=kundali_core_id,
            include_transits=include_transits,
        )

        cached = await self.get(key)
        if cached is None:
            return None

        return base64.b64decode(cached.encode("utf-8"))

    async def set_report(
        self,
        *,
        kundali_core_id: UUID,
        include_transits: bool,
        pdf_bytes: bytes,
    ) -> None:
        """
        Store PDF report in cache.
        """
        key = CacheKeys.report(
            kundali_core_id=kundali_core_id,
            include_transits=include_transits,
        )

        encoded = base64.b64encode(pdf_bytes).decode("utf-8")

        await self.set(
            key=key,
            value=encoded,
            ttl=CacheTTL.REPORT,
        )

    async def invalidate(
        self,
        *,
        kundali_core_id: UUID,
    ) -> None:
        """
        Invalidate cached reports for a kundali.
        """
        for include_transits in (True, False):
            key = CacheKeys.report(
                kundali_core_id=kundali_core_id,
                include_transits=include_transits,
            )
            await self.delete(key)
