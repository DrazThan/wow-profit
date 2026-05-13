from fastapi import APIRouter, HTTPException, Query

from app.services import item_db_service
from app.services.nexushub_service import nexushub_service

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("")
async def get_deals(
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    limit: int = Query(default=25, le=100),
):
    try:
        deals = await nexushub_service.get_deals(realm, faction)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    results = []
    for deal in deals[:limit]:
        item_id = deal.get("itemId")
        meta = await item_db_service.get_item(item_id) if item_id else None
        results.append({
            **deal,
            "name": meta.get("name", f"Item #{item_id}") if meta else f"Item #{item_id}",
            "icon_url": meta.get("icon_url") if meta else None,
            "quality": meta.get("quality", 1) if meta else 1,
        })

    return results
