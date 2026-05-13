import asyncio
import time

import httpx

from app.config import settings
from app.utils.cache import cache_get, cache_set

_rate_semaphore = asyncio.Semaphore(20)
_window_start: float = 0.0
_window_count: int = 0
_rate_lock = asyncio.Lock()

PRICE_TTL = 1800
HISTORY_TTL = 3600
DEAL_TTL = 1800
CRAFT_TTL = 3600


def _server_slug(realm: str, faction: str) -> str:
    return f"{realm.lower()}-{faction.lower()}"


class NexusHubService:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str) -> dict | list:
        global _window_start, _window_count
        async with _rate_lock:
            now = time.time()
            if now - _window_start >= 5.0:
                _window_start = now
                _window_count = 0
            if _window_count >= 20:
                sleep_for = 5.0 - (now - _window_start)
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
                _window_start = time.time()
                _window_count = 0
            _window_count += 1

        resp = await self._client.get(f"{settings.nexushub_base_url}{path}")
        resp.raise_for_status()
        return resp.json()

    async def get_prices(self, realm: str, faction: str, item_id: int) -> dict | None:
        server = _server_slug(realm, faction)
        key = f"nh:prices:{server}:{item_id}"
        cached = await cache_get(key)
        if cached:
            return cached
        try:
            data = await self._get(f"/prices/{server}/{item_id}")
            await cache_set(key, data, PRICE_TTL)
            return data
        except httpx.HTTPStatusError:
            return None

    async def get_history(self, realm: str, faction: str, item_id: int) -> list[dict]:
        server = _server_slug(realm, faction)
        key = f"nh:history:{server}:{item_id}"
        cached = await cache_get(key)
        if cached:
            return cached
        try:
            data = await self._get(f"/history/{server}/{item_id}")
            result = data.get("data", []) if isinstance(data, dict) else data
            await cache_set(key, result, HISTORY_TTL)
            return result
        except httpx.HTTPStatusError:
            return []

    async def get_deals(self, realm: str, faction: str) -> list[dict]:
        server = _server_slug(realm, faction)
        key = f"nh:deals:{server}"
        cached = await cache_get(key)
        if cached:
            return cached
        try:
            data = await self._get(f"/deals/{server}")
            result = data.get("data", []) if isinstance(data, dict) else data
            await cache_set(key, result, DEAL_TTL)
            return result
        except httpx.HTTPStatusError:
            return []

    async def get_crafting(self, realm: str, faction: str, item_id: int) -> dict | None:
        server = _server_slug(realm, faction)
        key = f"nh:crafting:{server}:{item_id}"
        cached = await cache_get(key)
        if cached:
            return cached
        try:
            data = await self._get(f"/crafting/{server}/{item_id}")
            await cache_set(key, data, CRAFT_TTL)
            return data
        except httpx.HTTPStatusError:
            return None

    async def search_items(self, query: str, limit: int = 10) -> list[dict]:
        key = f"nh:search:{query}:{limit}"
        cached = await cache_get(key)
        if cached:
            return cached
        try:
            data = await self._get(f"/items?search={query}&limit={limit}")
            result = data.get("data", []) if isinstance(data, dict) else data
            await cache_set(key, result, 3600)
            return result
        except httpx.HTTPStatusError:
            return []


nexushub_service = NexusHubService()
