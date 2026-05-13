from pydantic import BaseModel, Field


class ItemMeta(BaseModel):
    item_id: int
    name: str
    icon_url: str | None = None
    quality: int = 1
    vendor_sell: int = 0
    item_class: str | None = None
    item_subclass: str | None = None


class AHItemPrice(BaseModel):
    item_id: int
    name: str
    icon_url: str | None = None
    quality: int = 1
    # AH-level fields (from /ah/{id} bulk — always available)
    min_buyout: int = 0
    market_value: int = 0
    historical: int = 0        # TSM field name is "historical", not "historicalValue"
    num_auctions: int = 0
    quantity: int = 0
    # Region-level fields (from /region/{id}/item/{id} — fetched on-demand, 500/day limit)
    # TSM actual field names: avgSalePrice, salePct (0-100), soldPerDay
    avg_sale_price: int = 0
    sale_pct: int = 0          # 0–100 integer percentage
    sold_per_day: float = 0.0
    # Computed
    flip_margin: float = 0.0
    flip_profit: int = 0
    vendor_sell: int = 0


class WatchlistEntry(BaseModel):
    id: int
    item_id: int
    realm: str
    faction: str
    alert_below: int | None = None
    alert_above: int | None = None


class WatchlistCreate(BaseModel):
    item_id: int
    realm: str
    faction: str
    alert_below: int | None = None
    alert_above: int | None = None


class PriceHistory(BaseModel):
    timestamp: str
    min_buyout: int
    market_value: int


class ItemDetail(AHItemPrice):
    price_history: list[PriceHistory] = []
    crafting_cost: int | None = None
    crafting_profit: int | None = None
    crafting_roi: float | None = None
