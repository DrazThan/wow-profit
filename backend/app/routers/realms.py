from fastapi import APIRouter, HTTPException

from app.services.tsm_service import tsm_service

router = APIRouter(prefix="/api/realms", tags=["realms"])


@router.get("/regions")
async def get_regions():
    try:
        return await tsm_service.get_regions()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("")
async def get_realms(region_id: int):
    try:
        return await tsm_service.get_realms(region_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
