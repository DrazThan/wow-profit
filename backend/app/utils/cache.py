import asyncio
import time
from typing import Any

_store: dict[str, tuple[Any, float]] = {}
_lock = asyncio.Lock()

_redis_client = None


async def init_redis(url: str) -> None:
    global _redis_client
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, decode_responses=False)
        await client.ping()
        _redis_client = client
    except Exception:
        _redis_client = None


async def cache_get(key: str) -> Any | None:
    if _redis_client:
        try:
            import orjson
            val = await _redis_client.get(key)
            return orjson.loads(val) if val else None
        except Exception:
            pass

    async with _lock:
        entry = _store.get(key)
        if entry and time.time() < entry[1]:
            return entry[0]
        return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    if _redis_client:
        try:
            import orjson
            await _redis_client.setex(key, ttl, orjson.dumps(value))
            return
        except Exception:
            pass

    async with _lock:
        _store[key] = (value, time.time() + ttl)


async def cache_delete(key: str) -> None:
    if _redis_client:
        try:
            await _redis_client.delete(key)
        except Exception:
            pass

    async with _lock:
        _store.pop(key, None)
