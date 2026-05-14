from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.database import get_db
from app.models.price_snapshot import PriceSnapshot
from app.schemas.item import AHItemPrice, ItemDetail
from app.services import item_db_service
from app.services.item_db_service import get_item_local
from app.services.pricing_service import get_item_price, get_latest_prices
from app.utils.gold import flip_margin, flip_profit

router = APIRouter(prefix="/api/items", tags=["items"])


def _build_item(price_row: dict, meta: dict) -> AHItemPrice:
    mb = price_row["min_buyout"]
    mv = price_row["market_value"]
    return AHItemPrice(
        item_id=price_row["item_id"],
        name=meta.get("name", f"Item #{price_row['item_id']}"),
        icon_url=meta.get("icon_url"),
        quality=meta.get("quality", 1),
        min_buyout=mb,
        market_value=mv,
        num_auctions=0,
        quantity=price_row.get("quantity") or 0,
        flip_margin=flip_margin(mb, mv),
        flip_profit=flip_profit(mb, mv),
        vendor_sell=meta.get("vendor_sell", 0),
    )


@router.get("", response_model=list[AHItemPrice])
async def list_items(
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    min_margin: float | None = Query(default=None, ge=-1.0, le=1.0),
    quality: int | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    sort_by: str = Query(default="flip_profit"),
):
    async for db in get_db():
        rows = await get_latest_prices(realm, faction, db)

    if not rows:
        return []

    results: list[AHItemPrice] = []
    for row in rows:
        mb = row["min_buyout"]
        mv = row["market_value"]
        if mb == 0 or mv == 0:
            continue
        fm = flip_margin(mb, mv)
        if min_margin is not None and fm < min_margin:
            continue
        meta = get_item_local(row["item_id"])
        if quality is not None and meta.get("quality", 1) != quality:
            continue
        results.append(_build_item(row, meta))

    if sort_by == "flip_margin":
        results.sort(key=lambda x: x.flip_margin, reverse=True)
    else:
        results.sort(key=lambda x: x.flip_profit, reverse=True)

    return results[:limit]


@router.get("/search")
async def search_items(q: str = Query(..., min_length=1)):
    return await item_db_service.search_items(q)


@router.get("/{item_id}", response_model=ItemDetail)
async def get_item(
    item_id: int,
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
):
    async for db in get_db():
        price_row = await get_item_price(item_id, realm, faction, db)
        if not price_row:
            raise HTTPException(status_code=404, detail="Item not found in price data")

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = (
            select(PriceSnapshot)
            .where(
                PriceSnapshot.item_id == item_id,
                PriceSnapshot.realm == realm.lower(),
                PriceSnapshot.faction == faction.lower(),
                PriceSnapshot.recorded_at >= cutoff,
            )
            .order_by(PriceSnapshot.recorded_at)
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

    meta = await item_db_service.get_item(item_id) or {}
    base = _build_item(price_row, meta)

    history = [
        {
            "timestamp": s.recorded_at.isoformat(),
            "min_buyout": s.min_buyout or 0,
            "market_value": s.min_buyout or 0,
        }
        for s in snapshots
    ]

    return ItemDetail(**base.model_dump(), price_history=history)
