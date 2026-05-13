from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.recipe import Recipe
from app.schemas.crafting import CraftingRow, CraftingTreeNode, OptimizeRequest
from app.services import item_db_service
from app.services.nexushub_service import nexushub_service
from app.services.tsm_service import tsm_service

router = APIRouter(prefix="/api/crafting", tags=["crafting"])


async def _load_recipes(db) -> dict[int, Recipe]:
    stmt = select(Recipe).options(selectinload(Recipe.mats))
    result = await db.execute(stmt)
    recipes = result.scalars().all()
    return {r.output_item_id: r for r in recipes}


def _resolve_tree(
    item_id: int,
    qty: int,
    ah_prices: dict[int, int],
    recipes: dict[int, "Recipe"],
    overrides: dict[str, str],
    item_names: dict[int, str],
    item_icons: dict[int, str | None],
    visited: set[int],
    depth: int = 0,
) -> CraftingTreeNode:
    if depth > 10 or item_id in visited:
        ah_price = ah_prices.get(item_id, 0)
        return CraftingTreeNode(
            item_id=item_id,
            name=item_names.get(item_id, f"Item #{item_id}"),
            icon_url=item_icons.get(item_id),
            quantity_needed=qty,
            ah_price_each=ah_price,
            craft_cost_each=None,
            recipe_mats=None,
            mode="buy_only",
            total_cost=ah_price * qty,
        )

    ah_price = ah_prices.get(item_id, 0)
    recipe = recipes.get(item_id)

    if recipe is None:
        return CraftingTreeNode(
            item_id=item_id,
            name=item_names.get(item_id, f"Item #{item_id}"),
            icon_url=item_icons.get(item_id),
            quantity_needed=qty,
            ah_price_each=ah_price,
            craft_cost_each=None,
            recipe_mats=None,
            mode="buy_only",
            total_cost=ah_price * qty,
        )

    child_visited = visited | {item_id}
    resolved_mats = [
        _resolve_tree(
            mat.mat_item_id,
            mat.qty * qty,
            ah_prices,
            recipes,
            overrides,
            item_names,
            item_icons,
            child_visited,
            depth + 1,
        )
        for mat in recipe.mats
    ]

    total_mat_cost = sum(m.total_cost for m in resolved_mats)
    craft_cost_each = total_mat_cost // max(recipe.output_qty, 1)

    override = overrides.get(str(item_id))
    if override == "buy":
        mode = "forced_buy"
    elif override == "craft":
        mode = "forced_craft"
    elif craft_cost_each > 0 and ah_price > 0:
        mode = "craft" if craft_cost_each < ah_price else "buy"
    elif craft_cost_each > 0:
        mode = "craft"
    else:
        mode = "buy"

    if "craft" in mode:
        total_cost = craft_cost_each * qty
        savings_vs_buy = max(0, (ah_price - craft_cost_each) * qty)
        savings_vs_craft = 0
    else:
        total_cost = ah_price * qty
        savings_vs_buy = 0
        savings_vs_craft = max(0, (craft_cost_each - ah_price) * qty) if craft_cost_each else 0

    return CraftingTreeNode(
        item_id=item_id,
        name=item_names.get(item_id, f"Item #{item_id}"),
        icon_url=item_icons.get(item_id),
        quantity_needed=qty,
        ah_price_each=ah_price,
        craft_cost_each=craft_cost_each,
        recipe_mats=resolved_mats,
        mode=mode,
        total_cost=total_cost,
        savings_vs_buy=savings_vs_buy,
        savings_vs_craft=savings_vs_craft,
        profession=recipe.profession,
    )


async def _collect_item_ids(item_id: int, recipes: dict[int, Recipe], visited: set[int], depth: int = 0) -> set[int]:
    if depth > 10 or item_id in visited:
        return {item_id}
    ids = {item_id}
    recipe = recipes.get(item_id)
    if recipe:
        visited = visited | {item_id}
        for mat in recipe.mats:
            ids |= await _collect_item_ids(mat.mat_item_id, recipes, visited, depth + 1)
    return ids


@router.post("/optimize", response_model=CraftingTreeNode)
async def optimize_crafting(req: OptimizeRequest):
    async for db in get_db():
        try:
            ah_id = await tsm_service.get_ah_id(1, req.realm, req.faction)
            if not ah_id:
                raise HTTPException(status_code=404, detail="Auction house not found")
            ah_data = await tsm_service.get_ah_bulk_as_map(ah_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"TSM error: {e}")

        recipes = await _load_recipes(db)
        ah_prices = {iid: d.get("minBuyout", 0) for iid, d in ah_data.items()}

        all_ids = await _collect_item_ids(req.item_id, recipes, set())

        item_names: dict[int, str] = {}
        item_icons: dict[int, str | None] = {}
        for iid in all_ids:
            meta = await item_db_service.get_item(iid)
            if meta:
                item_names[iid] = meta.get("name", f"Item #{iid}")
                item_icons[iid] = meta.get("icon_url")

        tree = _resolve_tree(
            req.item_id,
            req.quantity,
            ah_prices,
            recipes,
            req.overrides,
            item_names,
            item_icons,
            set(),
        )
        return tree


@router.get("", response_model=list[CraftingRow])
async def list_crafting(
    realm: str = Query(default="faerlina"),
    faction: str = Query(default="horde"),
    profession: str | None = Query(default=None),
    min_roi: float = Query(default=0.0),
    limit: int = Query(default=50, le=200),
):
    async for db in get_db():
        stmt = select(Recipe).options(selectinload(Recipe.mats))
        if profession:
            stmt = stmt.where(Recipe.profession == profession)
        result = await db.execute(stmt)
        recipes = result.scalars().all()

        rows = []
        for recipe in recipes:
            try:
                craft_data = await nexushub_service.get_crafting(realm, faction, recipe.output_item_id)
                if not craft_data:
                    continue
                cost = craft_data.get("craftingCost", 0)
                profit = craft_data.get("profit", 0)
                mv = craft_data.get("marketValue", 0)
                roi = (profit / cost * 100) if cost > 0 else 0.0

                if roi < min_roi:
                    continue

                meta = await item_db_service.get_item(recipe.output_item_id)
                rows.append(
                    CraftingRow(
                        item_id=recipe.output_item_id,
                        name=meta.get("name", f"Item #{recipe.output_item_id}") if meta else f"Item #{recipe.output_item_id}",
                        icon_url=meta.get("icon_url") if meta else None,
                        profession=recipe.profession,
                        crafting_cost=cost,
                        market_value=mv,
                        profit=profit,
                        roi=roi,
                        mats=craft_data.get("mats", []),
                    )
                )
            except Exception:
                continue

        rows.sort(key=lambda r: r.roi, reverse=True)
        return rows[:limit]


@router.get("/professions")
async def list_professions():
    async for db in get_db():
        from sqlalchemy import distinct
        stmt = select(distinct(Recipe.profession)).where(Recipe.profession.is_not(None))
        result = await db.execute(stmt)
        return sorted([r for r in result.scalars().all() if r])
