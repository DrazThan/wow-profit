from fastapi import APIRouter, HTTPException, Query, UploadFile
from sqlalchemy import select, text

from app.config import settings
from app.database import get_db
from app.models.upload_log import UploadLog
from app.services.ingest_service import ingest_auctionator, ingest_tsm_appdata
from app.services.pricing_service import get_data_freshness

router = APIRouter(prefix="/api/upload", tags=["upload"])

_MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post("/auctionator")
async def upload_auctionator(file: UploadFile):
    raw = await file.read(_MAX_BYTES + 1)
    if len(raw) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    try:
        content = raw.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode file: {e}")

    if "AUCTIONATOR_PRICE_DATABASE" not in content:
        raise HTTPException(
            status_code=422,
            detail="File does not appear to be an Auctionator.lua SavedVariables file",
        )

    async for db in get_db():
        result = await ingest_auctionator(content, file.filename or "Auctionator.lua", db)

    if result.items_imported == 0:
        raise HTTPException(
            status_code=422,
            detail="No known items found in file. Is the item database seeded?",
        )

    return {
        "ok": True,
        "items_imported": result.items_imported,
        "items_skipped": result.items_skipped,
        "realms": result.realms,
    }


@router.post("/tsm-appdata")
async def upload_tsm_appdata(file: UploadFile):
    raw = await file.read(_MAX_BYTES + 1)
    if len(raw) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    try:
        content = raw.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode file: {e}")

    if "AUCTIONDB_MARKET_VALUE" not in content:
        raise HTTPException(
            status_code=422,
            detail="File does not appear to be a TSM AppData.lua file",
        )

    async for db in get_db():
        result = await ingest_tsm_appdata(content, file.filename or "AppData.lua", db)

    if result.items_imported == 0:
        raise HTTPException(status_code=422, detail="No price data found in file")

    return {
        "ok": True,
        "items_imported": result.items_imported,
        "realms": result.realms,
    }


@router.get("/status")
async def upload_status(
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
):
    async for db in get_db():
        return await get_data_freshness(realm, faction, db)


@router.get("/history")
async def upload_history(
    realm: str | None = Query(default=None),
    faction: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
):
    async for db in get_db():
        stmt = select(UploadLog).order_by(UploadLog.uploaded_at.desc()).limit(limit)
        if realm:
            stmt = stmt.where(UploadLog.realm == realm.lower())
        if faction:
            stmt = stmt.where(UploadLog.faction == faction.lower())
        result = await db.execute(stmt)
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "filename": log.filename,
                "upload_source": log.upload_source,
                "realm": log.realm,
                "faction": log.faction,
                "items_imported": log.items_imported,
                "items_skipped": log.items_skipped,
                "uploaded_at": log.uploaded_at.isoformat(),
            }
            for log in logs
        ]


@router.get("/realms")
async def uploaded_realms():
    """Returns distinct realm+faction pairs that have been uploaded."""
    async for db in get_db():
        sql = text("""
            SELECT DISTINCT realm, faction, MAX(uploaded_at) as last_upload
            FROM upload_logs
            GROUP BY realm, faction
            ORDER BY realm, faction
        """)
        result = await db.execute(sql)
        return [
            {"realm": row.realm, "faction": row.faction, "last_upload": row.last_upload.isoformat()}
            for row in result
        ]
