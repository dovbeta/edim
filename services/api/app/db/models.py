import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base


# =========================================================
# BUILDING
# =========================================================

class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    apartments: Mapped[List["Apartment"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )


# =========================================================
# APARTMENT
# =========================================================

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


# =========================================================
# USER
# =========================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    last_name: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    username: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        index=True,
        unique=True,
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


# =========================================================
# USER ↔ APARTMENT (M2M)
# =========================================================

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


# =========================================================
# CHAT IDENTITY
# =========================================================

class ChatIdentity(Base):
    __tablename__ = "chat_identities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    external_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship(
        back_populates="chat_identities"
    )

    __table_args__ = (
        UniqueConstraint(
            "channel",
            "external_id",
            name="uq_chat_identity_channel_external",
        ),
        Index("idx_chat_identity_user", "user_id"),
    )