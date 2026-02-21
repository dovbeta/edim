import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class UserUnit(Base):
    __tablename__ = "user_units"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    unit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped[str] = mapped_column(
        String,
        default="resident",
        nullable=False,
    )
    # owner | tenant | family | admin

    since: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="units"
    )

    unit: Mapped["Unit"] = relationship(
        back_populates="users"
    )

    __table_args__ = (
        Index("idx_user_unit_user", "user_id"),
        Index("idx_user_unit_unit", "unit_id"),
    )
