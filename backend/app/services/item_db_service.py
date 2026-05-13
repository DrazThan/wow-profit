import json
import os
from pathlib import Path

import httpx

from app.config import settings
from app.utils.cache import cache_get, cache_set

_items: dict[int, dict] = {}
_name_index: dict[str, list[int]] = {}
_name_to_id: dict[str, int] = {}  # lowercase name → item_id for Auctionator lookup


def _load_static_items() -> None:
    path = Path(settings.items_path)
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)
    for item in data:
        iid = item.get("itemId") or item.get("id")
        if iid:
            iid = int(iid)
            _items[iid] = item
            name_lower = item.get("name", "").lower()
            for word in name_lower.split():
                _name_index.setdefault(word, []).append(iid)
            # Prefer higher itemId on name collision (TBC items added later)
            if name_lower not in _name_to_id or iid > _name_to_id[name_lower]:
                _name_to_id[name_lower] = iid


async def get_item(item_id: int) -> dict | None:
    if item_id in _items:
        return _items[item_id]

    key = f"item_meta:{item_id}"
    cached = await cache_get(key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://www.wowhead.com/tooltip/item/{item_id}",
                params={"dataEnv": "4", "locale": "0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                item = {
                    "itemId": item_id,
                    "name": data.get("name", f"Item #{item_id}"),
                    "icon_url": f"https://wow.zamimg.com/images/wow/icons/large/{data.get('icon', 'inv_misc_questionmark')}.jpg",
                    "quality": data.get("quality", 1),
                    "vendor_sell": data.get("sellprice", 0),
                }
                _items[item_id] = item
                await cache_set(key, item, 86400)
                return item
    except Exception:
        pass

    fallback = {"itemId": item_id, "name": f"Item #{item_id}", "quality": 1, "vendor_sell": 0}
    return fallback


async def search_items(query: str, limit: int = 20) -> list[dict]:
    if not query:
        return []
    q = query.lower()
    matches: dict[int, int] = {}
    for word in q.split():
        for iid in _name_index.get(word, []):
            matches[iid] = matches.get(iid, 0) + 1

    scored = sorted(matches.items(), key=lambda x: -x[1])
    results = []
    for iid, _ in scored[:limit]:
        item = _items.get(iid)
        if item:
            results.append(item)
    return results


def get_all_items() -> list[dict]:
    return list(_items.values())


def resolve_item_id(name: str) -> int | None:
    """Look up itemId by item name (case-insensitive). Used for Auctionator name→id mapping."""
    name_lower = name.lower()
    if name_lower in _name_to_id:
        return _name_to_id[name_lower]
    # Fallback: strip non-alphanumeric and retry (handles color codes / minor variations)
    import re
    normalized = re.sub(r"[^a-z0-9 ']", "", name_lower).strip()
    return _name_to_id.get(normalized)


def init() -> None:
    _load_static_items()
