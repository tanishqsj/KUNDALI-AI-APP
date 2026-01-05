from typing import Any, Dict
from uuid import UUID

from app.cache.base import BaseCache
from app.cache.keys import CacheKeys
from app.cache.ttl import CacheTTL


class QueryCache(BaseCache):
    """
    Cache for ask / AI query responses.
    """

    async def get_answer(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
        question: str,
    ) -> Dict[str, Any] | None:
        """
        Fetch cached answer for a question.
        """
        key = CacheKeys.ask(
            user_id=user_id,
            kundali_core_id=kundali_core_id,
            question=question,
        )
        return await self.get(key)

    async def set_answer(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
        question: str,
        answer: Dict[str, Any],
    ) -> None:
        """
        Cache answer for a question.
        """
        key = CacheKeys.ask(
            user_id=user_id,
            kundali_core_id=kundali_core_id,
            question=question,
        )
        await self.set(
            key=key,
            value=answer,
            ttl=CacheTTL.ASK,
        )

    async def invalidate(
        self,
        *,
        user_id: UUID,
        kundali_core_id: UUID,
    ) -> None:
        """
        Invalidate all cached questions for a kundali.

        NOTE:
        Requires key pattern delete (to be handled separately).
        """
        # Pattern deletion intentionally not implemented here
        pass
