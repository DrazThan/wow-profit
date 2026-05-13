import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import AsyncSessionLocal, create_tables
from app.models.recipe import Recipe, RecipeMat
from app.routers import crafting, deals, items, realms, trends, watchlist
from app.services import item_db_service
from app.services.tsm_service import tsm_service
from app.services.nexushub_service import nexushub_service
from app.utils.cache import init_redis


async def _seed_recipes(session) -> None:
    from sqlalchemy import select, func as sqlfunc
    count_result = await session.execute(select(sqlfunc.count()).select_from(Recipe))
    count = count_result.scalar()
    if count and count > 0:
        return

    recipes_path = Path(settings.recipes_path)
    if not recipes_path.exists():
        recipes_path = Path(__file__).parent.parent.parent / "data" / "recipes.json"
    if not recipes_path.exists():
        return

    with open(recipes_path) as f:
        data = json.load(f)

    for rec in data:
        recipe = Recipe(
            output_item_id=rec["outputItemId"],
            output_qty=rec.get("outputQty", 1),
            profession=rec.get("profession"),
            skill_required=rec.get("skillRequired"),
            source=rec.get("source"),
        )
        session.add(recipe)
        await session.flush()

        for mat in rec.get("mats", []):
            session.add(RecipeMat(
                recipe_id=recipe.id,
                mat_item_id=mat["itemId"],
                qty=mat["qty"],
            ))

    await session.commit()


async def _snapshot_job() -> None:
    while True:
        await asyncio.sleep(3600)
        try:
            from app.database import AsyncSessionLocal
            from app.models.price_snapshot import PriceSnapshot
            ah_id = await tsm_service.get_ah_id(1, settings.default_realm)
            if not ah_id:
                continue
            bulk = await tsm_service.get_ah_bulk(ah_id)
            async with AsyncSessionLocal() as db:
                for item in bulk[:500]:
                    iid = item.get("itemId")
                    if not iid:
                        continue
                    db.add(PriceSnapshot(
                        item_id=iid,
                        realm=settings.default_realm,
                        faction=settings.default_faction,
                        min_buyout=item.get("minBuyout"),
                        market_value=item.get("marketValue"),
                        num_auctions=item.get("numAuctions"),
                        quantity=item.get("quantity"),
                    ))
                await db.commit()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.redis_url:
        await init_redis(settings.redis_url)

    await create_tables()

    item_db_service.init()

    async with AsyncSessionLocal() as db:
        await _seed_recipes(db)

    asyncio.create_task(_snapshot_job())

    yield

    await tsm_service.close()
    await nexushub_service.close()


app = FastAPI(
    title="WoW Profit Tracker",
    description="TBC Classic Auction House profit tracker",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(realms.router)
app.include_router(items.router)
app.include_router(deals.router)
app.include_router(trends.router)
app.include_router(crafting.router)
app.include_router(watchlist.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
