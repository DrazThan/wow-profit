from sqlalchemy import ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    output_item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    output_qty: Mapped[int] = mapped_column(SmallInteger, default=1)
    profession: Mapped[str | None] = mapped_column(String(50))
    skill_required: Mapped[int | None] = mapped_column(SmallInteger)
    source: Mapped[str | None] = mapped_column(String(100))

    mats: Mapped[list["RecipeMat"]] = relationship(
        "RecipeMat", back_populates="recipe", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_recipes_output", "output_item_id"),)


class RecipeMat(Base):
    __tablename__ = "recipe_mats"

    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    mat_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    qty: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="mats")

    __table_args__ = (Index("idx_recipe_mats_mat", "mat_item_id"),)
