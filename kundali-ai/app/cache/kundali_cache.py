from typing import Any, Dict
from uuid import UUID

from app.cache.base import BaseCache
from app.cache.keys import CacheKeys
from app.cache.ttl import CacheTTL


class KundaliCache(BaseCache):
    """
    Cache for kundali core + derived + divisional data.

    Used by:
    - KundaliService
    - Ask API
    - ReportService
    """

    async def get_kundali(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
    ) -> Dict[str, Any] | None:
        """
        Fetch kundali snapshot from cache.
        """
        key = CacheKeys.kundali(user_id, kundali_core_id)
        return await self.get(key)

    async def set_kundali(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
        data: Dict[str, Any],
    ) -> None:
        """
        Store kundali snapshot in cache.
        """
        key = CacheKeys.kundali(user_id, kundali_core_id)
        await self.set(
            key=key,
            value=data,
            ttl=CacheTTL.KUNDALI,
        )

    async def invalidate(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
    ) -> None:
        """
        Invalidate cached kundali.
        """
        key = CacheKeys.kundali(user_id, kundali_core_id)
        await self.delete(key)
