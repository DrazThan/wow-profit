"""
Background item-metadata seeding.

After a scan upload, we fire-and-forget a task that fetches
Wowhead metadata for every item_id not yet in the items table,
then upserts the results.  Progress is tracked in a module-level
dict so the /api/items/seed-status endpoint can report it.
"""

import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal
from app.models.item import Item
from app.services import item_db_service

_WOWHEAD_URL = "https://nether.wowhead.com/tooltip/item/{item_id}"
_WOWHEAD_PARAMS = {"locale": "0"}
_CONCURRENCY = 8

_state: dict = {
    "running": False,
    "total": 0,
    "seeded": 0,
    "failed": 0,
}
_task = None  # keep a reference so the GC doesn't collect it


def get_seed_status() -> dict:
    pending = max(0, _state["total"] - _state["seeded"] - _state["failed"])
    return {
        "seeding": _state["running"],
        "total": _state["total"],
        "seeded": _state["seeded"],
        "failed": _state["failed"],
        "pending": pending,
    }


async def _fetch_one(client: httpx.AsyncClient, item_id: int) -> dict | None:
    try:
        resp = await client.get(
            _WOWHEAD_URL.format(item_id=item_id),
            params=_WOWHEAD_PARAMS,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        name = data.get("name", "")
        if not name:
            return None
        return {
            "item_id": item_id,
            "name": name,
            "icon_url": f"https://wow.zamimg.com/images/wow/icons/large/{data.get('icon', 'inv_misc_questionmark')}.jpg",
            "quality": data.get("quality", 1),
            "vendor_sell": data.get("sellprice", 0),
        }
    except Exception:
        return None


async def _seed_task(unknown: list[int]) -> None:

    sem = asyncio.Semaphore(_CONCURRENCY)
    results: list[dict] = []

    async def fetch_bounded(client: httpx.AsyncClient, iid: int) -> None:  # noqa: E306
        async with sem:
            item = await _fetch_one(client, iid)
            if item:
                item_db_service.cache_item(iid, item)
                results.append(item)
                _state["seeded"] += 1
            else:
                _state["failed"] += 1

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        await asyncio.gather(*(fetch_bounded(client, iid) for iid in unknown))

    if results:
        async with AsyncSessionLocal() as db:
            for item in results:
                stmt = (
                    pg_insert(Item)
                    .values(
                        item_id=item["item_id"],
                        name=item["name"],
                        icon_url=item["icon_url"],
                        quality=item["quality"],
                        vendor_sell=item["vendor_sell"],
                        updated_at=datetime.now(timezone.utc),
                    )
                    .on_conflict_do_update(
                        index_elements=["item_id"],
                        set_={
                            "name": item["name"],
                            "icon_url": item["icon_url"],
                            "quality": item["quality"],
                            "vendor_sell": item["vendor_sell"],
                            "updated_at": datetime.now(timezone.utc),
                        },
                    )
                )
                await db.execute(stmt)
            await db.commit()

    _state["running"] = False


def trigger_seeding(item_ids: list[int]) -> None:
    """Fire-and-forget: seed metadata for any item_ids not yet in the local cache."""
    global _task
    if _state["running"]:
        return
    unknown = [iid for iid in item_ids if not item_db_service.item_exists_local(iid)]
    if not unknown:
        return
    # Update state synchronously so status endpoint reflects it immediately
    _state.update(running=True, total=len(unknown), seeded=0, failed=0)
    _task = asyncio.create_task(_seed_task(unknown))
