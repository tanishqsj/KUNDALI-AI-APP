import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis

from app.config import settings


class RedisClient:
    """
    Async Redis client wrapper.
    """

    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,  # store strings, not bytes
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
        return cls._client

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def serialize(value: Any) -> str:
        def custom_encoder(obj):
            if isinstance(obj, UUID):
                return str(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        return json.dumps(value, default=custom_encoder)

    @staticmethod
    def deserialize(value: str) -> Any:
        return json.loads(value)
