"""AI assistant: builds resident-aware context and calls OpenAI."""
from __future__ import annotations

from openai import OpenAI

from edim.models import Announcement, Resident

_SYSTEM_TEMPLATE = """\
You are E-DIM Copilot — a helpful personal assistant for residents of apartment buildings \
managed by an OSBB (homeowners association).

Current resident profile:
- Name: {full_name}
- Apartment: {apartment_number}
- Building address: {building_address}

Recent building announcements:
{announcements_section}

Always answer in the language the resident uses. Be concise, friendly, and specific to their \
building context when relevant. If you don't know something, say so honestly.\
"""

_NO_ANNOUNCEMENTS = "  (no announcements yet)"


def _format_announcements(announcements: list[Announcement]) -> str:
    if not announcements:
        return _NO_ANNOUNCEMENTS
    lines = []
    for ann in announcements:
        date_str = ann.created_at.strftime("%Y-%m-%d") if ann.created_at else "unknown date"
        lines.append(f"  [{date_str}] {ann.title}: {ann.body}")
    return "\n".join(lines)


def build_system_prompt(resident: Resident, announcements: list[Announcement]) -> str:
    """Return the system prompt personalised for *resident*."""
    return _SYSTEM_TEMPLATE.format(
        full_name=resident.full_name,
        apartment_number=resident.apartment_number,
        building_address=resident.building.address,
        announcements_section=_format_announcements(announcements),
    )


def ask(
    client: OpenAI,
    model: str,
    system_prompt: str,
    conversation_history: list[dict[str, str]],
    user_message: str,
) -> str:
    """Send a message to the OpenAI API and return the assistant reply."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=model, messages=messages)  # type: ignore[arg-type]
    return response.choices[0].message.content or ""
