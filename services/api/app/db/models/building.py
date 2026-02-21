import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    external_id: Mapped[str] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="buildings"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    units: Mapped[List["Unit"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )
