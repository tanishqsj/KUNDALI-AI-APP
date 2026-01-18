import asyncio
from typing import Optional, List

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.config import settings


class LLMClientError(Exception):
    """Base exception for LLM client errors."""


class LLMClient:
    """
    Low-level async LLM client.

    This class:
    - talks to the LLM provider
    - handles retries & timeouts
    - returns raw text only
    """

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )

        self.model = model or settings.OPENAI_MODEL
        self.temperature = (
            temperature
            if temperature is not None
            else settings.OPENAI_TEMPERATURE
        )
        self.max_tokens = (
            max_tokens
            if max_tokens is not None
            else settings.OPENAI_MAX_TOKENS
        )

        self.timeout = settings.OPENAI_TIMEOUT
        self.retries = settings.OPENAI_RETRIES

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Generate a completion from the LLM.
        """
        for attempt in range(1, self.retries + 1):
            try:
                response = await asyncio.wait_for(
                    self._call_llm(system_prompt, user_prompt),
                    timeout=self.timeout,
                )
                return response

            except asyncio.TimeoutError:
                if attempt == self.retries:
                    raise LLMClientError("LLM request timed out")
                await asyncio.sleep(self._backoff(attempt))

            except Exception as exc:
                if attempt == self.retries:
                    raise LLMClientError(str(exc))
                await asyncio.sleep(self._backoff(attempt))

        raise LLMClientError("LLM request failed")

    async def complete_stream(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ):
        """
        Generate a streaming completion from the LLM.
        Yields chunks of text.
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            raise LLMClientError(f"Streaming failed: {str(e)}")

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text, with caching.
        """
        if not text:
            return []

        # 1. Check cache
        import hashlib
        import json
        from app.cache.redis import RedisClient

        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        cache_key = f"embedding:{text_hash}"
        
        try:
            redis_client = RedisClient.get_client()
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            # Log error but continue to fetch from API
            print(f"⚠️ [Redis] Cache read failed: {e}")

        # 2. Fetch from API
        try:
            response = await self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # 3. Store in cache (Async, fire-and-forget-ish)
            try:
                await redis_client.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(embedding)
                )
            except Exception as e:
                print(f"⚠️ [Redis] Cache write failed: {e}")
                
            return embedding
        except Exception as e:
            raise LLMClientError(f"Embedding failed: {str(e)}")

    # ─────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Perform the actual LLM call.
        """

        completion: ChatCompletion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return completion.choices[0].message.content.strip()

    def _backoff(self, attempt: int) -> float:
        """
        Exponential backoff (simple).
        """
        return min(2 ** attempt, 10)
