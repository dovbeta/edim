"""SQLAlchemy database models for E-DIM Copilot."""
from __future__ import annotations

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base."""


class Building(Base):
    """An apartment building managed by an OSBB."""

    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    residents: Mapped[list[Resident]] = relationship(
        "Resident", back_populates="building", cascade="all, delete-orphan"
    )
    announcements: Mapped[list[Announcement]] = relationship(
        "Announcement", back_populates="building", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Building id={self.id} address={self.address!r}>"


class Resident(Base):
    """A resident of an apartment in a building."""

    __tablename__ = "residents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    apartment_number: Mapped[str] = mapped_column(String(20), nullable=False)
    building_id: Mapped[int] = mapped_column(Integer, ForeignKey("buildings.id"), nullable=False)

    building: Mapped[Building] = relationship("Building", back_populates="residents")

    def __repr__(self) -> str:
        return (
            f"<Resident id={self.id} telegram_id={self.telegram_id}"
            f" name={self.full_name!r} apt={self.apartment_number!r}>"
        )


class Announcement(Base):
    """A building-wide announcement or event."""

    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(Integer, ForeignKey("buildings.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    building: Mapped[Building] = relationship("Building", back_populates="announcements")

    def __repr__(self) -> str:
        return f"<Announcement id={self.id} title={self.title!r}>"
