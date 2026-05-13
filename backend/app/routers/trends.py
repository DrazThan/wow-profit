from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.database import get_db
from app.models.price_snapshot import PriceSnapshot

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/{item_id}")
async def get_trends(
    item_id: int,
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    days: int = Query(default=14, ge=1, le=90),
):
    async for db in get_db():
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
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

        if not snapshots:
            return []

        return [
            {
                "timestamp": s.recorded_at.isoformat(),
                "min_buyout": s.min_buyout or 0,
                "market_value": s.min_buyout or 0,
                "num_auctions": s.num_auctions or 0,
                "quantity": s.quantity or 0,
            }
            for s in snapshots
        ]
