#!/usr/bin/env python3
"""
Fetch item metadata from Wowhead for all item IDs in the price_snapshots table
and merge into data/items.json.

Usage:
    cd backend
    python scripts/seed_items.py [--db-url postgresql+asyncpg://...] [--limit 5000]

Requires: httpx, asyncpg (already in pyproject.toml deps)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import asyncpg
import httpx

ITEMS_JSON = Path(__file__).parent.parent.parent / "data" / "items.json"
WOWHEAD_TOOLTIP = "https://www.wowhead.com/tooltip/item/{item_id}"
WOWHEAD_PARAMS = {"dataEnv": "4", "locale": "0"}  # TBC Classic


async def fetch_item(client: httpx.AsyncClient, item_id: int) -> dict | None:
    try:
        resp = await client.get(
            WOWHEAD_TOOLTIP.format(item_id=item_id),
            params=WOWHEAD_PARAMS,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        name = data.get("name", "")
        if not name:
            return None
        return {
            "itemId": item_id,
            "name": name,
            "icon_url": f"https://wow.zamimg.com/images/wow/icons/large/{data.get('icon', 'inv_misc_questionmark')}.jpg",
            "quality": data.get("quality", 1),
            "vendor_sell": data.get("sellprice", 0),
        }
    except Exception as e:
        print(f"  Error fetching {item_id}: {e}", file=sys.stderr)
        return None


async def main(db_url: str, limit: int, concurrency: int) -> None:
    print(f"Loading existing items from {ITEMS_JSON} ...")
    existing: dict[int, dict] = {}
    if ITEMS_JSON.exists():
        with open(ITEMS_JSON) as f:
            for item in json.load(f):
                iid = item.get("itemId") or item.get("id")
                if iid:
                    existing[int(iid)] = item
    print(f"  {len(existing)} items already in items.json")

    print("Connecting to database ...")
    conn_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(conn_url)
    rows = await conn.fetch(
        "SELECT DISTINCT item_id FROM price_snapshots ORDER BY item_id LIMIT $1",
        limit,
    )
    await conn.close()
    all_ids = [r["item_id"] for r in rows]
    missing = [iid for iid in all_ids if iid not in existing]
    print(f"  {len(all_ids)} distinct item IDs in DB, {len(missing)} missing from items.json")

    if not missing:
        print("Nothing to fetch.")
        return

    print(f"Fetching {len(missing)} items from Wowhead (concurrency={concurrency}) ...")
    semaphore = asyncio.Semaphore(concurrency)
    fetched: list[dict] = []
    failed: list[int] = []

    async def bounded_fetch(client: httpx.AsyncClient, item_id: int) -> None:
        async with semaphore:
            result = await fetch_item(client, item_id)
            if result:
                fetched.append(result)
            else:
                failed.append(item_id)
            done = len(fetched) + len(failed)
            if done % 100 == 0:
                print(f"  {done}/{len(missing)} ({len(fetched)} ok, {len(failed)} failed)")

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(bounded_fetch(client, iid) for iid in missing))

    print(f"Done: {len(fetched)} fetched, {len(failed)} failed")

    for item in fetched:
        existing[item["itemId"]] = item

    with open(ITEMS_JSON, "w") as f:
        json.dump(list(existing.values()), f, separators=(",", ":"))

    print(f"Saved {len(existing)} items to {ITEMS_JSON}")
    if failed:
        print(f"Failed IDs (first 20): {failed[:20]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-url",
        default="postgresql+asyncpg://ahtracker:ahtracker@localhost:5432/ah_tracker",
    )
    parser.add_argument("--limit", type=int, default=50000)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(main(args.db_url, args.limit, args.concurrency))
