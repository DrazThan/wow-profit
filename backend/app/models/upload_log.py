from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_source: Mapped[str] = mapped_column(String(50), nullable=False)  # "auctionator" | "tsm_appdata"
    realm: Mapped[str] = mapped_column(String(100), nullable=False)
    faction: Mapped[str] = mapped_column(String(10), nullable=False)
    items_imported: Mapped[int] = mapped_column(Integer, default=0)
    items_skipped: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_upload_logs_realm_faction", "realm", "faction", "uploaded_at"),
    )
