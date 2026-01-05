from typing import Any, Optional

from app.cache.redis import RedisClient


class BaseCache:
    """
    Base cache abstraction.

    All cache implementations should extend this class.
    """

    def __init__(self):
        self.client = RedisClient.get_client()

    # ─────────────────────────────────────────────
    # Core operations
    # ─────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        Returns None if key does not exist.
        """
        value = await self.client.get(key)
        if value is None:
            return None
        return RedisClient.deserialize(value)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int,
    ) -> None:
        """
        Set value in cache with TTL (seconds).
        """
        serialized = RedisClient.serialize(value)
        await self.client.setex(
            key,
            ttl,
            serialized,
        )

    async def delete(self, key: str) -> None:
        """
        Delete a cache key.
        """
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        """
        return bool(await self.client.exists(key))
