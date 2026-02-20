"""Database session management and CRUD operations."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from edim.models import Announcement, Base, Building, Resident


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create engine, initialize schema, and return a session factory."""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=True, autocommit=False)


# ---------------------------------------------------------------------------
# Building helpers
# ---------------------------------------------------------------------------


def get_or_create_building(session: Session, address: str, name: str | None = None) -> Building:
    """Return an existing building by address or create a new one."""
    building = session.query(Building).filter_by(address=address).first()
    if building is None:
        building = Building(address=address, name=name)
        session.add(building)
        session.flush()
    return building


# ---------------------------------------------------------------------------
# Resident helpers
# ---------------------------------------------------------------------------


def get_resident_by_telegram_id(session: Session, telegram_id: int) -> Resident | None:
    """Return the resident for the given Telegram user ID, or None."""
    return session.query(Resident).filter_by(telegram_id=telegram_id).first()


def create_or_update_resident(
    session: Session,
    telegram_id: int,
    full_name: str,
    apartment_number: str,
    building: Building,
) -> Resident:
    """Insert or fully replace a resident's profile."""
    resident = get_resident_by_telegram_id(session, telegram_id)
    if resident is None:
        resident = Resident(
            telegram_id=telegram_id,
            full_name=full_name,
            apartment_number=apartment_number,
            building_id=building.id,
        )
        session.add(resident)
    else:
        resident.full_name = full_name
        resident.apartment_number = apartment_number
        resident.building_id = building.id
    session.flush()
    return resident


# ---------------------------------------------------------------------------
# Announcement helpers
# ---------------------------------------------------------------------------


def get_latest_announcements(
    session: Session, building_id: int, limit: int = 5
) -> list[Announcement]:
    """Return the most recent announcements for a building."""
    return (
        session.query(Announcement)
        .filter_by(building_id=building_id)
        .order_by(Announcement.created_at.desc())
        .limit(limit)
        .all()
    )


def create_announcement(
    session: Session, building_id: int, title: str, body: str
) -> Announcement:
    """Create and persist a new announcement."""
    announcement = Announcement(building_id=building_id, title=title, body=body)
    session.add(announcement)
    session.flush()
    return announcement
