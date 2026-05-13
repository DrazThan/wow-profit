from fastapi import APIRouter

from app.database import get_db
from app.routers.upload import uploaded_realms

router = APIRouter(prefix="/api/realms", tags=["realms"])


@router.get("")
async def get_realms():
    """Returns realm+faction pairs that have upload data."""
    async for db in get_db():
        from sqlalchemy import text
        sql = text("""
            SELECT DISTINCT realm, faction, MAX(uploaded_at) as last_upload
            FROM upload_logs
            GROUP BY realm, faction
            ORDER BY realm, faction
        """)
        result = await db.execute(sql)
        rows = result.all()
        return [
            {"realm": row.realm, "faction": row.faction, "last_upload": row.last_upload.isoformat()}
            for row in rows
        ]
