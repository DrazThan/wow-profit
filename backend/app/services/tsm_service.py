import asyncio
import time

import httpx

from app.config import settings
from app.utils.cache import cache_get, cache_set

# Rate limits per the TSM docs (per 24 hours):
#   /ah/{id}                   → 100/day
#   /ah/{id}/item/{itemId}     → 500/day
#   /region/{id}/item/{itemId} → 500/day
#   /region/{id}               → 10/day
# Cache aggressively to stay well inside these limits.
AH_BULK_TTL = 3600       # 1 hour — at most 24 bulk fetches/day (well under 100/day limit)
REGION_ALL_TTL = 86400   # 24 hours — region-all is 10/day, only fetch once per day
REALM_TTL = 86400


class TSMService:
    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _refresh_token(self) -> None:
        if not settings.tsm_api_key or settings.tsm_api_key == "your_tsm_api_key_here":
            raise RuntimeError(
                "TSM_API_KEY is not configured. Get your key at "
                "https://id.tradeskillmaster.com/realms/app/account"
            )
        resp = await self._client.post(
            settings.tsm_auth_url,
            json={
                "client_id": "c260f00d-1071-409a-992f-dda2e5498536",
                "grant_type": "api_token",
                "scope": "app:realm-api app:pricing-api",
                "token": settings.tsm_api_key,
            },
        )
        if resp.status_code == 401:
            raise RuntimeError("TSM authentication failed — check your TSM_API_KEY")
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        # expires_in from TSM is 86400 (24h). Buffer 5 minutes to refresh proactively.
        self._token_expires_at = time.time() + data.get("expires_in", 86400) - 300

    async def _get_token(self) -> str:
        async with self._lock:
            if not self._token or time.time() >= self._token_expires_at:
                await self._refresh_token()
            return self._token  # type: ignore[return-value]

    def _invalidate_token(self) -> None:
        self._token = None
        self._token_expires_at = 0.0

    async def _get(self, url: str, params: dict | None = None) -> dict | list:
        token = await self._get_token()
        resp = await self._client.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 401:
            # Token was revoked — clear it and retry once with a fresh one
            async with self._lock:
                self._invalidate_token()
            token = await self._get_token()
            resp = await self._client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            raise RuntimeError(f"TSM rate limit hit, retry after {retry_after}s")
        resp.raise_for_status()
        return resp.json()

    async def get_regions(self) -> list[dict]:
        cached = await cache_get("tsm:regions")
        if cached:
            return cached
        data = await self._get(f"{settings.tsm_realm_api_url}/regions")
        await cache_set("tsm:regions", data, REALM_TTL)
        return data

    async def get_realms(self, region_id: int) -> list[dict]:
        key = f"tsm:realms:{region_id}"
        cached = await cache_get(key)
        if cached:
            return cached
        # Correct URL per TSM docs: /regions/{regionId}/realms
        data = await self._get(f"{settings.tsm_realm_api_url}/regions/{region_id}/realms")
        await cache_set(key, data, REALM_TTL)
        return data

    async def get_ah_id(self, region_id: int, realm_name: str, faction: str = "horde") -> int | None:
        """
        Looks up auctionHouseId by searching the realms list for a matching realm name,
        then picking the AH whose type matches the requested faction.
        For Classic: type is "Alliance", "Horde", or "Neutral".
        For Retail: type is "All".
        """
        key = f"tsm:ahid:{region_id}:{realm_name}:{faction}"
        cached = await cache_get(key)
        if cached is not None:
            return cached

        realms = await self.get_realms(region_id)
        name_lower = realm_name.lower()
        faction_type = faction.capitalize()  # "Horde" or "Alliance"

        for realm in realms:
            if realm.get("name", "").lower() != name_lower:
                continue
            ah_houses = realm.get("auctionHouses", [])
            # Prefer exact faction match, fall back to "All" (Retail / merged AH)
            for ah in ah_houses:
                if ah.get("type", "").lower() == faction.lower():
                    ah_id = ah["auctionHouseId"]
                    await cache_set(key, ah_id, REALM_TTL)
                    return ah_id
            for ah in ah_houses:
                if ah.get("type") == "All":
                    ah_id = ah["auctionHouseId"]
                    await cache_set(key, ah_id, REALM_TTL)
                    return ah_id

        return None

    async def get_ah_bulk(self, ah_id: int) -> list[dict]:
        key = f"tsm:ah_bulk:{ah_id}"
        cached = await cache_get(key)
        if cached:
            return cached
        data = await self._get(f"{settings.tsm_pricing_api_url}/ah/{ah_id}")
        items = data if isinstance(data, list) else data.get("items", [])
        await cache_set(key, items, AH_BULK_TTL)
        return items

    async def get_ah_bulk_as_map(self, ah_id: int) -> dict[int, dict]:
        items = await self.get_ah_bulk(ah_id)
        return {item["itemId"]: item for item in items if "itemId" in item}

    async def get_item_price(self, ah_id: int, item_id: int) -> dict | None:
        bulk = await self.get_ah_bulk_as_map(ah_id)
        return bulk.get(item_id)

    async def get_region_item(self, region_id: int, item_id: int) -> dict | None:
        key = f"tsm:region:{region_id}:{item_id}"
        cached = await cache_get(key)
        if cached:
            return cached
        data = await self._get(
            f"{settings.tsm_pricing_api_url}/region/{region_id}/item/{item_id}"
        )
        await cache_set(key, data, 3600)
        return data


tsm_service = TSMService()
