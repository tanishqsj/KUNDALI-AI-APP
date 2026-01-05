from typing import Dict, Any, Optional
from uuid import UUID

from app.cache.base import BaseCache
from app.cache.keys import CacheKeys
from app.cache.ttl import CacheTTL


class TransitCache(BaseCache):
    """
    Cache for current transit & gochar data.
    """

    async def get_transits(
        self,
        *,
        kundali_core_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch cached transit data.
        """
        key = CacheKeys.transit(kundali_core_id)
        return await self.get(key)

    async def set_transits(
        self,
        *,
        kundali_core_id: UUID,
        data: Dict[str, Any],
    ) -> None:
        """
        Store transit data in cache.
        """
        key = CacheKeys.transit(kundali_core_id)
        await self.set(
            key=key,
            value=data,
            ttl=CacheTTL.TRANSIT,
        )

    async def invalidate(
        self,
        *,
        kundali_core_id: UUID,
    ) -> None:
        """
        Invalidate cached transit data.
        """
        key = CacheKeys.transit(kundali_core_id)
        await self.delete(key)
