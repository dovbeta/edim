import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    integration_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="api",
    )
    # api | file | manual

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    integration_config: Mapped[dict] = mapped_column(
        postgresql.JSONB,
        nullable=True,
    )

    last_import_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
    )

    organizations: Mapped[List["Organization"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
    )