from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CraftingTreeNode(BaseModel):
    item_id: int
    name: str
    quantity_needed: int
    ah_price_each: int
    craft_cost_each: int | None = None
    recipe_mats: list[CraftingTreeNode] | None = None
    mode: Literal["buy", "craft", "forced_buy", "forced_craft", "buy_only"]
    total_cost: int
    savings_vs_buy: int = 0
    savings_vs_craft: int = 0
    icon_url: str | None = None
    profession: str | None = None


CraftingTreeNode.model_rebuild()


class OptimizeRequest(BaseModel):
    item_id: int
    quantity: int = 1
    realm: str
    faction: str
    overrides: dict[str, Literal["buy", "craft"]] = {}


class CraftingRow(BaseModel):
    item_id: int
    name: str
    icon_url: str | None = None
    profession: str | None = None
    crafting_cost: int
    market_value: int
    profit: int
    roi: float
    mats: list[dict]
