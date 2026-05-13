from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_latest_prices(realm: str, faction: str, db: AsyncSession) -> list[dict]:
    """
    Returns list of {item_id, min_buyout, market_value, recorded_at} for
    all items that have snapshots for this realm+faction.

    min_buyout = most recent snapshot value
    market_value = 14-day rolling average of the daily minimum, or min_buyout if no history
    """
    sql = text("""
        WITH latest_snap AS (
            SELECT DISTINCT ON (item_id)
                item_id, min_buyout, recorded_at
            FROM price_snapshots
            WHERE realm = :realm AND faction = :faction AND min_buyout > 0
            ORDER BY item_id, recorded_at DESC
        ),
        market_vals AS (
            SELECT item_id, CAST(AVG(daily_min) AS BIGINT) AS market_value
            FROM (
                SELECT item_id,
                       DATE(recorded_at) AS day,
                       MIN(min_buyout) AS daily_min
                FROM price_snapshots
                WHERE realm = :realm AND faction = :faction
                  AND min_buyout > 0
                  AND recorded_at > NOW() - INTERVAL '14 days'
                GROUP BY item_id, DATE(recorded_at)
            ) sub
            GROUP BY item_id
        )
        SELECT l.item_id,
               l.min_buyout,
               l.recorded_at,
               COALESCE(m.market_value, l.min_buyout) AS market_value
        FROM latest_snap l
        LEFT JOIN market_vals m ON l.item_id = m.item_id
    """)

    result = await db.execute(sql, {"realm": realm.lower(), "faction": faction.lower()})
    rows = result.mappings().all()
    return [dict(r) for r in rows]


async def get_item_price(item_id: int, realm: str, faction: str, db: AsyncSession) -> dict | None:
    """
    Returns {item_id, min_buyout, market_value, recorded_at} for a single item,
    or None if no snapshots exist.
    """
    sql = text("""
        WITH latest_snap AS (
            SELECT item_id, min_buyout, recorded_at
            FROM price_snapshots
            WHERE item_id = :item_id AND realm = :realm AND faction = :faction
              AND min_buyout > 0
            ORDER BY recorded_at DESC
            LIMIT 1
        ),
        market_val AS (
            SELECT CAST(AVG(daily_min) AS BIGINT) AS market_value
            FROM (
                SELECT DATE(recorded_at) AS day, MIN(min_buyout) AS daily_min
                FROM price_snapshots
                WHERE item_id = :item_id AND realm = :realm AND faction = :faction
                  AND min_buyout > 0
                  AND recorded_at > NOW() - INTERVAL '14 days'
                GROUP BY DATE(recorded_at)
            ) sub
        )
        SELECT l.item_id,
               l.min_buyout,
               l.recorded_at,
               COALESCE(m.market_value, l.min_buyout) AS market_value
        FROM latest_snap l, market_val m
    """)

    result = await db.execute(
        sql, {"item_id": item_id, "realm": realm.lower(), "faction": faction.lower()}
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_ah_prices_map(realm: str, faction: str, db: AsyncSession) -> dict[int, int]:
    """Returns {item_id: min_buyout} for the most recent snapshot per item."""
    sql = text("""
        SELECT DISTINCT ON (item_id) item_id, min_buyout
        FROM price_snapshots
        WHERE realm = :realm AND faction = :faction AND min_buyout > 0
        ORDER BY item_id, recorded_at DESC
    """)
    result = await db.execute(sql, {"realm": realm.lower(), "faction": faction.lower()})
    return {row.item_id: row.min_buyout for row in result}


async def get_last_upload(realm: str, faction: str, db: AsyncSession) -> dict | None:
    """Returns info about the most recent upload for a realm+faction."""
    sql = text("""
        SELECT realm, faction, items_imported, uploaded_at, filename, upload_source
        FROM upload_logs
        WHERE realm = :realm AND faction = :faction
        ORDER BY uploaded_at DESC
        LIMIT 1
    """)
    result = await db.execute(sql, {"realm": realm.lower(), "faction": faction.lower()})
    row = result.mappings().first()
    return dict(row) if row else None


async def get_data_freshness(realm: str, faction: str, db: AsyncSession) -> dict:
    """
    Returns freshness state:
      fresh   = data is < 2 hours old
      stale   = 2–24 hours old
      old     = 1–7 days old
      no_data = no uploads exist for this realm+faction
    """
    last = await get_last_upload(realm, faction, db)
    if not last:
        return {"state": "no_data", "last_upload": None, "realm": realm, "faction": faction}

    uploaded_at: datetime = last["uploaded_at"]
    if uploaded_at.tzinfo is None:
        uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - uploaded_at).total_seconds() / 3600

    if age_hours < 2:
        state = "fresh"
    elif age_hours < 24:
        state = "stale"
    elif age_hours < 168:
        state = "old"
    else:
        state = "no_data"

    return {
        "state": state,
        "last_upload": uploaded_at.isoformat(),
        "age_hours": round(age_hours, 1),
        "realm": realm,
        "faction": faction,
        "items_imported": last["items_imported"],
    }
