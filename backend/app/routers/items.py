from fastapi import APIRouter, HTTPException, Query

from app.schemas.item import AHItemPrice, ItemDetail, WatchlistCreate, WatchlistEntry
from app.services import item_db_service, nexushub_service, tsm_service as tsm
from app.utils.gold import flip_margin, flip_profit

router = APIRouter(prefix="/api/items", tags=["items"])


async def _enrich_item(raw: dict, region_data: dict | None = None, meta: dict | None = None) -> AHItemPrice:
    """
    raw: AH-level data from /ah/{id} bulk. Actual TSM field names:
         itemId, minBuyout, marketValue, historical, numAuctions, quantity
    region_data: optional region-level data from /region/{id}/item/{id}. Actual TSM field names:
         avgSalePrice, salePct (0-100), soldPerDay, historical
    """
    item_id = raw.get("itemId", 0)
    if meta is None:
        meta = await item_db_service.get_item(item_id) or {}
    mb = raw.get("minBuyout", 0)
    mv = raw.get("marketValue", 0)
    rd = region_data or {}
    return AHItemPrice(
        item_id=item_id,
        name=meta.get("name", f"Item #{item_id}"),
        icon_url=meta.get("icon_url"),
        quality=meta.get("quality", 1),
        min_buyout=mb,
        market_value=mv,
        historical=raw.get("historical", 0),
        num_auctions=raw.get("numAuctions", 0),
        quantity=raw.get("quantity", 0),
        avg_sale_price=rd.get("avgSalePrice", 0),
        sale_pct=rd.get("salePct", 0),
        sold_per_day=rd.get("soldPerDay", 0.0),
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
        ah_id = await tsm.tsm_service.get_ah_id(region_id, realm, faction)
        if not ah_id:
            raise HTTPException(status_code=404, detail="Auction house not found for realm/faction")
        bulk = await tsm.tsm_service.get_ah_bulk(ah_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Filter — region fields (sale_pct, sold_per_day) are not in bulk AH data;
    # min_sale_rate and min_daily_sold filters only apply if those were fetched separately.
    results = []
    for raw in bulk:
        mb = raw.get("minBuyout", 0)
        mv = raw.get("marketValue", 0)
        if mb == 0 or mv == 0:
            continue
        if flip_margin(mb, mv) < min_margin:
            continue
        results.append(raw)

    results.sort(key=lambda r: flip_profit(r.get("minBuyout", 0), r.get("marketValue", 0)), reverse=True)
    results = results[:limit]

    enriched = [await _enrich_item(raw) for raw in results]

    if sort_by == "flip_margin":
        enriched.sort(key=lambda x: x.flip_margin, reverse=True)
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
        ah_id = await tsm.tsm_service.get_ah_id(region_id, realm, faction)
        if not ah_id:
            raise HTTPException(status_code=404, detail="Auction house not found")
        raw = await tsm.tsm_service.get_item_price(ah_id, item_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not raw:
        raise HTTPException(status_code=404, detail="Item not found on AH")

    # Fetch region-level data for the detail view (salePct, soldPerDay, avgSalePrice)
    region_data = None
    try:
        region_data = await tsm.tsm_service.get_region_item(region_id, item_id)
    except Exception:
        pass

    base = await _enrich_item(raw, region_data=region_data)

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
