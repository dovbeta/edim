import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class UserApartment(Base):
    __tablename__ = "user_apartments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    apartment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("apartments.id", ondelete="CASCADE"),
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
        back_populates="apartments"
    )

    apartment: Mapped["Apartment"] = relationship(
        back_populates="residents"
    )

    __table_args__ = (
        Index("idx_user_apartment_user", "user_id"),
        Index("idx_user_apartment_apartment", "apartment_id"),
    )
