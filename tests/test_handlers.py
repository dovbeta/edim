"""Unit tests for Telegram bot handlers (no live Telegram connection)."""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from edim.handlers import (
    REG_ADDRESS,
    REG_APT,
    REG_NAME,
    events,
    myinfo,
    register_address,
    register_apt,
    register_name,
    register_start,
    start,
)
from edim.models import Announcement, Building, Resident
from edim.storage import create_session_factory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def session_factory():
    return create_session_factory("sqlite:///:memory:")


def _make_update(text: str = "", user_id: int = 1) -> MagicMock:
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_user.id = user_id
    return update


def _make_context(session_factory=None, extra_bot_data=None) -> MagicMock:
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    if session_factory:
        context.bot_data["session_factory"] = session_factory
    if extra_bot_data:
        context.bot_data.update(extra_bot_data)
    return context


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_sends_welcome():
    update = _make_update()
    context = _make_context()
    await start(update, context)
    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "E-DIM Copilot" in call_text


# ---------------------------------------------------------------------------
# /register flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_start_asks_for_name():
    update = _make_update()
    context = _make_context()
    state = await register_start(update, context)
    assert state == REG_NAME
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_register_name_stores_name():
    update = _make_update(text="Ivan Petrenko")
    context = _make_context()
    context.user_data["registration"] = {}
    state = await register_name(update, context)
    assert state == REG_APT
    assert context.user_data["registration"]["full_name"] == "Ivan Petrenko"


@pytest.mark.asyncio
async def test_register_apt_stores_apt():
    update = _make_update(text="42")
    context = _make_context()
    context.user_data["registration"] = {"full_name": "Ivan"}
    state = await register_apt(update, context)
    assert state == REG_ADDRESS
    assert context.user_data["registration"]["apartment_number"] == "42"


@pytest.mark.asyncio
async def test_register_address_persists_resident(session_factory):
    update = _make_update(text="Main St. 1, Kyiv", user_id=99)
    context = _make_context(session_factory=session_factory)
    context.user_data["registration"] = {
        "full_name": "Ivan Petrenko",
        "apartment_number": "42",
    }
    from telegram.ext import ConversationHandler

    state = await register_address(update, context)
    assert state == ConversationHandler.END

    from edim.storage import get_resident_by_telegram_id

    with session_factory() as session:
        resident = get_resident_by_telegram_id(session, 99)
    assert resident is not None
    assert resident.full_name == "Ivan Petrenko"
    assert resident.apartment_number == "42"


# ---------------------------------------------------------------------------
# /myinfo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_myinfo_not_registered(session_factory):
    update = _make_update(user_id=555)
    context = _make_context(session_factory=session_factory)
    await myinfo(update, context)
    call_text = update.message.reply_text.call_args[0][0]
    assert "not registered" in call_text.lower()


@pytest.mark.asyncio
async def test_myinfo_shows_profile(session_factory):
    from edim.storage import create_or_update_resident, get_or_create_building

    with session_factory() as session:
        building = get_or_create_building(session, "Oak Ave. 1")
        create_or_update_resident(session, 888, "Olena Kovalenko", "7", building)
        session.commit()

    update = _make_update(user_id=888)
    context = _make_context(session_factory=session_factory)
    await myinfo(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Olena Kovalenko" in call_text
    assert "7" in call_text


# ---------------------------------------------------------------------------
# /events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_events_no_announcements(session_factory):
    from edim.storage import create_or_update_resident, get_or_create_building

    with session_factory() as session:
        building = get_or_create_building(session, "Elm St. 3")
        create_or_update_resident(session, 777, "Taras Bondarenko", "5", building)
        session.commit()

    update = _make_update(user_id=777)
    context = _make_context(session_factory=session_factory)
    await events(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "no announcements" in call_text.lower()


@pytest.mark.asyncio
async def test_events_shows_announcement(session_factory):
    from edim.storage import (
        create_announcement,
        create_or_update_resident,
        get_or_create_building,
    )

    with session_factory() as session:
        building = get_or_create_building(session, "Elm St. 4")
        create_or_update_resident(session, 666, "Maria Shevchenko", "3", building)
        create_announcement(session, building.id, "Roof repair", "Starts Monday")
        session.commit()

    update = _make_update(user_id=666)
    context = _make_context(session_factory=session_factory)
    await events(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Roof repair" in call_text
