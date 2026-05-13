from pydantic import BaseModel


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
    min_buyout: int = 0
    market_value: int = 0       # 14-day rolling avg of daily min (computed locally)
    num_auctions: int = 0
    quantity: int = 0
    sale_pct: int = 0
    sold_per_day: float = 0.0
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
