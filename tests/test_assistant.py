"""Unit tests for the AI assistant module."""
import datetime
from unittest.mock import MagicMock, patch

import pytest

from edim.assistant import _format_announcements, ask, build_system_prompt
from edim.models import Announcement, Building, Resident


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_resident(full_name="Ivan Petrenko", apartment="42", address="Main St. 1") -> Resident:
    building = Building(id=1, address=address)
    resident = Resident(
        id=1,
        telegram_id=100,
        full_name=full_name,
        apartment_number=apartment,
        building_id=1,
    )
    resident.building = building
    return resident


def _make_announcement(title: str, body: str) -> Announcement:
    ann = Announcement(id=1, building_id=1, title=title, body=body)
    ann.created_at = datetime.datetime(2024, 5, 1, 10, 0, 0)
    return ann


# ---------------------------------------------------------------------------
# _format_announcements
# ---------------------------------------------------------------------------


def test_format_announcements_empty():
    result = _format_announcements([])
    assert "no announcements" in result


def test_format_announcements_includes_title():
    ann = _make_announcement("Water shut-off", "Friday 9–18")
    result = _format_announcements([ann])
    assert "Water shut-off" in result
    assert "Friday 9–18" in result
    assert "2024-05-01" in result


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------


def test_build_system_prompt_contains_resident_info():
    resident = _make_resident()
    prompt = build_system_prompt(resident, [])
    assert "Ivan Petrenko" in prompt
    assert "42" in prompt
    assert "Main St. 1" in prompt


def test_build_system_prompt_contains_announcement():
    resident = _make_resident()
    ann = _make_announcement("Annual meeting", "15 June at 18:00")
    prompt = build_system_prompt(resident, [ann])
    assert "Annual meeting" in prompt
    assert "15 June at 18:00" in prompt


# ---------------------------------------------------------------------------
# ask
# ---------------------------------------------------------------------------


def test_ask_returns_assistant_content():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Hello, Ivan!"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    result = ask(
        client=mock_client,
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant.",
        conversation_history=[],
        user_message="Who are you?",
    )

    assert result == "Hello, Ivan!"
    mock_client.chat.completions.create.assert_called_once()


def test_ask_passes_history_to_api():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Sure!"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]

    ask(
        client=mock_client,
        model="gpt-4o-mini",
        system_prompt="System",
        conversation_history=history,
        user_message="Tell me more",
    )

    call_messages = mock_client.chat.completions.create.call_args[1]["messages"]
    roles = [m["role"] for m in call_messages]
    assert roles == ["system", "user", "assistant", "user"]
