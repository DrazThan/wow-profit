from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select

from app.database import get_db
from app.models.watchlist import Watchlist
from app.schemas.item import WatchlistCreate, WatchlistEntry
from app.services import item_db_service
from app.services.pricing_service import get_item_price
from app.utils.gold import flip_profit

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("")
async def get_watchlist(realm: str = "faerlina", faction: str = "horde"):
    async for db in get_db():
        result = await db.execute(
            select(Watchlist).where(Watchlist.realm == realm, Watchlist.faction == faction)
        )
        entries = result.scalars().all()

        results = []
        for entry in entries:
            price_row = await get_item_price(entry.item_id, realm, faction, db)
            meta = await item_db_service.get_item(entry.item_id) or {}
            mb = price_row["min_buyout"] if price_row else 0
            mv = price_row["market_value"] if price_row else 0
            alert = None
            if entry.alert_below and mb > 0 and mb <= entry.alert_below:
                alert = "below"
            elif entry.alert_above and mv > 0 and mv >= entry.alert_above:
                alert = "above"

            results.append({
                "id": entry.id,
                "item_id": entry.item_id,
                "name": meta.get("name", f"Item #{entry.item_id}"),
                "icon_url": meta.get("icon_url"),
                "realm": entry.realm,
                "faction": entry.faction,
                "alert_below": entry.alert_below,
                "alert_above": entry.alert_above,
                "min_buyout": mb,
                "market_value": mv,
                "flip_profit": flip_profit(mb, mv),
                "alert": alert,
            })

        return results


@router.post("", response_model=WatchlistEntry, status_code=201)
async def add_to_watchlist(body: WatchlistCreate):
    async for db in get_db():
        entry = Watchlist(
            item_id=body.item_id,
            realm=body.realm,
            faction=body.faction,
            alert_below=body.alert_below,
            alert_above=body.alert_above,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return WatchlistEntry(
            id=entry.id,
            item_id=entry.item_id,
            realm=entry.realm,
            faction=entry.faction,
            alert_below=entry.alert_below,
            alert_above=entry.alert_above,
        )


@router.delete("/{entry_id}", status_code=204)
async def remove_from_watchlist(entry_id: int):
    async for db in get_db():
        result = await db.execute(delete(Watchlist).where(Watchlist.id == entry_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        await db.commit()
