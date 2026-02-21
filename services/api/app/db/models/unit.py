import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    number: Mapped[str] = mapped_column(String, nullable=False)

    external_id: Mapped[str] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    unit_type: Mapped[str] = mapped_column(
        String,
        default="apartment",
        nullable=False,
    )

    building_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    section: Mapped[str | None] = mapped_column(String, nullable=True)
    floor: Mapped[int | None] = mapped_column(nullable=True)

    area_total: Mapped[float | None] = mapped_column(nullable=True)

    rooms: Mapped[int | None] = mapped_column(nullable=True)

    personal_account: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    building: Mapped["Building"] = relationship(
        back_populates="units"
    )

    users: Mapped[List["UserUnit"]] = relationship(
        back_populates="unit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "number",
            "unit_type",
            name="uq_unit_building_number_type",
        ),
    )
