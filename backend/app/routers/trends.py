from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.database import get_db
from app.models.price_snapshot import PriceSnapshot
from app.services.nexushub_service import nexushub_service

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/{item_id}")
async def get_trends(
    item_id: int,
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    days: int = Query(default=14, ge=1, le=90),
):
    async for db in get_db():
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(PriceSnapshot)
            .where(
                PriceSnapshot.item_id == item_id,
                PriceSnapshot.realm == realm,
                PriceSnapshot.faction == faction,
                PriceSnapshot.recorded_at >= cutoff,
            )
            .order_by(PriceSnapshot.recorded_at)
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()

        if snapshots:
            return [
                {
                    "timestamp": s.recorded_at.isoformat(),
                    "min_buyout": s.min_buyout,
                    "market_value": s.market_value,
                    "num_auctions": s.num_auctions,
                    "quantity": s.quantity,
                }
                for s in snapshots
            ]

    history = await nexushub_service.get_history(realm, faction, item_id)
    return [
        {
            "timestamp": h.get("scannedAt", ""),
            "min_buyout": h.get("minBuyout", 0),
            "market_value": h.get("marketValue", 0),
            "num_auctions": h.get("numAuctions", 0),
            "quantity": h.get("quantity", 0),
        }
        for h in history
    ]
