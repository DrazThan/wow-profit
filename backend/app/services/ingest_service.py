from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_snapshot import PriceSnapshot
from app.models.upload_log import UploadLog
from app.services import item_db_service
from app.services.lua_parser_service import parse_auctionator_lua, parse_tsm_appdata_lua


class IngestResult:
    def __init__(self) -> None:
        self.items_imported = 0
        self.items_skipped = 0
        self.realms: list[str] = []

    def to_dict(self) -> dict:
        return {
            "items_imported": self.items_imported,
            "items_skipped": self.items_skipped,
            "realms": self.realms,
        }


async def ingest_auctionator(
    content: str,
    filename: str,
    db: AsyncSession,
) -> IngestResult:
    parsed = parse_auctionator_lua(content)
    result = IngestResult()
    snapshot_time = datetime.now(timezone.utc)

    for realm_faction, items in parsed.items():
        # Split "Faerlina - Horde" into realm="faerlina", faction="horde"
        parts = realm_faction.rsplit(" - ", 1)
        realm = parts[0].strip().lower()
        faction = parts[1].strip().lower() if len(parts) > 1 else "unknown"

        realm_imported = 0
        realm_skipped = 0

        for item_name, (min_buyout, _scan_ts) in items.items():
            item_id = item_db_service.resolve_item_id(item_name)
            if item_id is None:
                realm_skipped += 1
                continue
            db.add(PriceSnapshot(
                item_id=item_id,
                realm=realm,
                faction=faction,
                min_buyout=min_buyout,
                recorded_at=snapshot_time,
            ))
            realm_imported += 1

        if realm_imported > 0:
            db.add(UploadLog(
                filename=filename,
                upload_source="auctionator",
                realm=realm,
                faction=faction,
                items_imported=realm_imported,
                items_skipped=realm_skipped,
            ))
            result.realms.append(f"{realm} - {faction}")

        result.items_imported += realm_imported
        result.items_skipped += realm_skipped

    await db.commit()
    return result


async def ingest_tsm_appdata(
    content: str,
    filename: str,
    db: AsyncSession,
) -> IngestResult:
    parsed = parse_tsm_appdata_lua(content)
    result = IngestResult()
    snapshot_time = datetime.now(timezone.utc)

    for realm_slug, items in parsed.items():
        realm_imported = 0

        for item_id, price_data in items.items():
            min_buyout = price_data.get("min_buyout", 0)
            if min_buyout <= 0:
                continue
            db.add(PriceSnapshot(
                item_id=item_id,
                realm=realm_slug.lower(),
                faction="all",
                min_buyout=min_buyout,
                recorded_at=snapshot_time,
            ))
            realm_imported += 1

        if realm_imported > 0:
            db.add(UploadLog(
                filename=filename,
                upload_source="tsm_appdata",
                realm=realm_slug.lower(),
                faction="all",
                items_imported=realm_imported,
                items_skipped=0,
            ))
            result.realms.append(realm_slug.lower())

        result.items_imported += realm_imported

    await db.commit()
    return result
