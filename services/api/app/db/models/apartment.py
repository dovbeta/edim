import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Apartment(Base):
    __tablename__ = "apartments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    number: Mapped[str] = mapped_column(String, nullable=False)

    building_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    building: Mapped["Building"] = relationship(
        back_populates="apartments"
    )

    residents: Mapped[List["UserApartment"]] = relationship(
        back_populates="apartment",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "number",
            name="uq_apartment_building_number",
        ),
    )