import asyncio
import time

import httpx

from app.config import settings
from app.utils.cache import cache_get, cache_set

AH_BULK_TTL = 3600
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
        resp = await self._client.post(
            settings.tsm_auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": "TSM_API_CLIENT",
                "scope": "app:pricing-api",
                "token": settings.tsm_api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    async def _get_token(self) -> str:
        async with self._lock:
            if not self._token or time.time() >= self._token_expires_at:
                await self._refresh_token()
            return self._token  # type: ignore[return-value]

    async def _get(self, url: str, params: dict | None = None) -> dict | list:
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
        data = await self._get(
            f"{settings.tsm_realm_api_url}/realms", params={"regionId": region_id}
        )
        await cache_set(key, data, REALM_TTL)
        return data

    async def get_ah_id(self, region_id: int, realm_name: str) -> int | None:
        key = f"tsm:ahid:{region_id}:{realm_name}"
        cached = await cache_get(key)
        if cached is not None:
            return cached
        data = await self._get(
            f"{settings.tsm_realm_api_url}/ah",
            params={"regionId": region_id, "realmName": realm_name},
        )
        ah_id = data.get("auctionHouseId") if isinstance(data, dict) else None
        if ah_id:
            await cache_set(key, ah_id, REALM_TTL)
        return ah_id

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
