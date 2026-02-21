import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[Optional[str]] = mapped_column(String)
    last_name: Mapped[Optional[str]] = mapped_column(String)
    username: Mapped[Optional[str]] = mapped_column(String)

    phone: Mapped[Optional[str]] = mapped_column(
        String,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    apartments: Mapped[List["UserApartment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    chat_identities: Mapped[List["ChatIdentity"]] = relationship(
        back_populates="user"
    )