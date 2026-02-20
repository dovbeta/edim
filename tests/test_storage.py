"""Unit tests for the storage layer (in-memory SQLite)."""
import pytest
from sqlalchemy.orm import Session

from edim.models import Base
from edim.storage import (
    create_announcement,
    create_or_update_resident,
    create_session_factory,
    get_latest_announcements,
    get_or_create_building,
    get_resident_by_telegram_id,
)


@pytest.fixture()
def session_factory():
    """Return an in-memory session factory with fresh schema."""
    return create_session_factory("sqlite:///:memory:")


@pytest.fixture()
def session(session_factory):
    with session_factory() as s:
        yield s


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------


def test_get_or_create_building_creates_new(session: Session):
    building = get_or_create_building(session, "Shevchenko St. 1, Kyiv")
    session.commit()
    assert building.id is not None
    assert building.address == "Shevchenko St. 1, Kyiv"


def test_get_or_create_building_idempotent(session: Session):
    b1 = get_or_create_building(session, "Shevchenko St. 1, Kyiv")
    session.commit()
    b2 = get_or_create_building(session, "Shevchenko St. 1, Kyiv")
    session.commit()
    assert b1.id == b2.id


def test_get_or_create_building_stores_name(session: Session):
    building = get_or_create_building(session, "Main St. 5", name="Tower A")
    session.commit()
    assert building.name == "Tower A"


# ---------------------------------------------------------------------------
# Resident
# ---------------------------------------------------------------------------


def test_create_resident(session: Session):
    building = get_or_create_building(session, "Main St. 5")
    resident = create_or_update_resident(
        session, telegram_id=111, full_name="Ivan Petrenko", apartment_number="42", building=building
    )
    session.commit()
    assert resident.id is not None
    assert resident.telegram_id == 111
    assert resident.full_name == "Ivan Petrenko"
    assert resident.apartment_number == "42"


def test_get_resident_by_telegram_id_found(session: Session):
    building = get_or_create_building(session, "Main St. 5")
    create_or_update_resident(session, 222, "Olena Kovalenko", "7", building)
    session.commit()
    found = get_resident_by_telegram_id(session, 222)
    assert found is not None
    assert found.full_name == "Olena Kovalenko"


def test_get_resident_by_telegram_id_not_found(session: Session):
    assert get_resident_by_telegram_id(session, 999) is None


def test_update_resident(session: Session):
    building = get_or_create_building(session, "Main St. 5")
    create_or_update_resident(session, 333, "Old Name", "1", building)
    session.commit()

    create_or_update_resident(session, 333, "New Name", "2", building)
    session.commit()

    resident = get_resident_by_telegram_id(session, 333)
    assert resident.full_name == "New Name"
    assert resident.apartment_number == "2"


# ---------------------------------------------------------------------------
# Announcement
# ---------------------------------------------------------------------------


def test_create_announcement(session: Session):
    building = get_or_create_building(session, "Oak Ave. 10")
    session.commit()
    ann = create_announcement(session, building.id, "Water shut-off", "Water will be off on Friday")
    session.commit()
    assert ann.id is not None
    assert ann.title == "Water shut-off"


def test_get_latest_announcements_empty(session: Session):
    building = get_or_create_building(session, "Oak Ave. 11")
    session.commit()
    result = get_latest_announcements(session, building.id)
    assert result == []


def test_get_latest_announcements_limit(session: Session):
    building = get_or_create_building(session, "Oak Ave. 12")
    session.commit()
    for i in range(7):
        create_announcement(session, building.id, f"Title {i}", f"Body {i}")
    session.commit()
    result = get_latest_announcements(session, building.id, limit=5)
    assert len(result) == 5
