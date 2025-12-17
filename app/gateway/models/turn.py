from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db_base import Base

class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    user_text: Mapped[str] = mapped_column(Text, nullable=False)

    assistant_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    ttft_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ttaf_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
