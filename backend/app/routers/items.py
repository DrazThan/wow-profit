from fastapi import APIRouter, HTTPException, Query

from app.schemas.item import AHItemPrice, ItemDetail, WatchlistCreate, WatchlistEntry
from app.services import item_db_service, nexushub_service, tsm_service as tsm
from app.utils.gold import flip_margin, flip_profit

router = APIRouter(prefix="/api/items", tags=["items"])


async def _enrich_item(raw: dict, realm: str, faction: str) -> AHItemPrice:
    item_id = raw.get("itemId", 0)
    meta = await item_db_service.get_item(item_id) or {}
    mb = raw.get("minBuyout", 0)
    mv = raw.get("marketValue", 0)
    return AHItemPrice(
        item_id=item_id,
        name=meta.get("name", f"Item #{item_id}"),
        icon_url=meta.get("icon_url"),
        quality=meta.get("quality", 1),
        min_buyout=mb,
        market_value=mv,
        historical_value=raw.get("historicalValue", 0),
        num_auctions=raw.get("numAuctions", 0),
        quantity=raw.get("quantity", 0),
        region_min_buyout_avg=raw.get("regionMinBuyoutAvg", 0),
        region_market_value_avg=raw.get("regionMarketValueAvg", 0),
        region_sale_avg=raw.get("regionSaleAvg", 0),
        region_sale_rate=raw.get("regionSaleRate", 0.0),
        region_avg_daily_sold=raw.get("regionAvgDailySold", 0.0),
        flip_margin=flip_margin(mb, mv),
        flip_profit=flip_profit(mb, mv),
        vendor_sell=meta.get("vendor_sell", 0),
    )


@router.get("", response_model=list[AHItemPrice])
async def list_items(
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    region_id: int = Query(default=1),
    min_margin: float = Query(default=0.0, ge=0.0, le=1.0),
    min_sale_rate: float = Query(default=0.0, ge=0.0, le=1.0),
    min_daily_sold: float = Query(default=0.0, ge=0.0),
    quality: int | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    sort_by: str = Query(default="flip_profit"),
):
    try:
        ah_id = await tsm.tsm_service.get_ah_id(region_id, realm)
        if not ah_id:
            raise HTTPException(status_code=404, detail="Auction house not found for realm")
        bulk = await tsm.tsm_service.get_ah_bulk(ah_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    results = []
    for raw in bulk:
        mb = raw.get("minBuyout", 0)
        mv = raw.get("marketValue", 0)
        sr = raw.get("regionSaleRate", 0.0)
        ds = raw.get("regionAvgDailySold", 0.0)
        if mb == 0 or mv == 0:
            continue
        margin = flip_margin(mb, mv)
        if margin < min_margin:
            continue
        if sr < min_sale_rate:
            continue
        if ds < min_daily_sold:
            continue
        results.append(raw)

    results.sort(key=lambda r: flip_profit(r.get("minBuyout", 0), r.get("marketValue", 0)), reverse=True)
    results = results[:limit]

    enriched = []
    for raw in results:
        enriched.append(await _enrich_item(raw, realm, faction))

    if sort_by == "flip_margin":
        enriched.sort(key=lambda x: x.flip_margin, reverse=True)
    elif sort_by == "region_sale_rate":
        enriched.sort(key=lambda x: x.region_sale_rate, reverse=True)
    elif sort_by == "region_avg_daily_sold":
        enriched.sort(key=lambda x: x.region_avg_daily_sold, reverse=True)
    else:
        enriched.sort(key=lambda x: x.flip_profit, reverse=True)

    return enriched


@router.get("/search")
async def search_items(q: str = Query(..., min_length=1)):
    return await item_db_service.search_items(q)


@router.get("/{item_id}", response_model=ItemDetail)
async def get_item(
    item_id: int,
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    region_id: int = Query(default=1),
):
    try:
        ah_id = await tsm.tsm_service.get_ah_id(region_id, realm)
        if not ah_id:
            raise HTTPException(status_code=404, detail="Auction house not found")
        raw = await tsm.tsm_service.get_item_price(ah_id, item_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not raw:
        raise HTTPException(status_code=404, detail="Item not found on AH")

    base = await _enrich_item(raw, realm, faction)

    history_raw = await nexushub_service.nexushub_service.get_history(realm, faction, item_id)
    history = [
        {"timestamp": h.get("scannedAt", ""), "min_buyout": h.get("minBuyout", 0), "market_value": h.get("marketValue", 0)}
        for h in history_raw
    ]

    craft_data = await nexushub_service.nexushub_service.get_crafting(realm, faction, item_id)
    crafting_cost = craft_data.get("craftingCost") if craft_data else None
    crafting_profit = craft_data.get("profit") if craft_data else None
    crafting_roi = craft_data.get("roi") if craft_data else None

    return ItemDetail(
        **base.model_dump(),
        price_history=history,
        crafting_cost=crafting_cost,
        crafting_profit=crafting_profit,
        crafting_roi=crafting_roi,
    )
