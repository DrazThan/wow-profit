from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(Text)
    item_class: Mapped[str | None] = mapped_column(String(50))
    item_subclass: Mapped[str | None] = mapped_column(String(50))
    quality: Mapped[int | None] = mapped_column(SmallInteger)
    vendor_sell: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
