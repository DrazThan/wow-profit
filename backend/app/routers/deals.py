from fastapi import APIRouter, Query

from app.database import get_db
from app.services import item_db_service
from app.services.pricing_service import get_latest_prices
from app.utils.gold import flip_margin, flip_profit

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("")
async def get_deals(
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    min_margin: float = Query(default=0.10),
    limit: int = Query(default=25, le=100),
):
    async for db in get_db():
        rows = await get_latest_prices(realm, faction, db)

    deals = []
    for row in rows:
        mb = row["min_buyout"]
        mv = row["market_value"]
        fm = flip_margin(mb, mv)
        fp = flip_profit(mb, mv)
        if fm < min_margin or fp <= 0:
            continue
        meta = await item_db_service.get_item(row["item_id"]) or {}
        deals.append({
            "item_id": row["item_id"],
            "name": meta.get("name", f"Item #{row['item_id']}"),
            "icon_url": meta.get("icon_url"),
            "quality": meta.get("quality", 1),
            "min_buyout": mb,
            "market_value": mv,
            "flip_profit": fp,
            "flip_margin": fm,
        })

    deals.sort(key=lambda x: x["flip_profit"], reverse=True)
    return deals[:limit]
