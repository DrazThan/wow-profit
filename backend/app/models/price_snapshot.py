from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    realm: Mapped[str] = mapped_column(String(100), nullable=False)
    faction: Mapped[str] = mapped_column(String(10), nullable=False)
    min_buyout: Mapped[int | None] = mapped_column(BigInteger)
    market_value: Mapped[int | None] = mapped_column(BigInteger)
    num_auctions: Mapped[int | None] = mapped_column(Integer)
    quantity: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_snapshots_item_realm", "item_id", "realm", "faction", "recorded_at"),
    )
