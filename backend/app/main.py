import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import AsyncSessionLocal, create_tables
from app.models.recipe import Recipe, RecipeMat
from app.models.upload_log import UploadLog  # noqa: F401 — ensure table is created
from app.routers import crafting, deals, items, realms, trends, upload, watchlist
from app.services import item_db_service
from app.utils.cache import init_redis


async def _seed_recipes(session) -> None:
    from sqlalchemy import func as sqlfunc, select

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.redis_url:
        await init_redis(settings.redis_url)

    await create_tables()

    item_db_service.init()

    async with AsyncSessionLocal() as db:
        await _seed_recipes(db)

    yield


app = FastAPI(
    title="WoW Profit Tracker",
    description="TBC Classic Auction House profit tracker — Auctionator.lua upload model",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(realms.router)
app.include_router(items.router)
app.include_router(deals.router)
app.include_router(trends.router)
app.include_router(crafting.router)
app.include_router(watchlist.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
