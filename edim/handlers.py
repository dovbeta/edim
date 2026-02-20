"""Telegram bot command and message handlers."""
from __future__ import annotations

import logging

import openai
from openai import OpenAI
from sqlalchemy.orm import Session, sessionmaker
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from edim import assistant, storage
from edim.config import Config

logger = logging.getLogger(__name__)

# ConversationHandler states for /register
REG_NAME, REG_APT, REG_ADDRESS = range(3)

# Per-user key for in-progress registration data
_REG_KEY = "registration"
# Per-user key for conversation history sent to OpenAI
_HISTORY_KEY = "chat_history"
_MAX_HISTORY = 10  # keep last N turns (user+assistant pairs)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and explain how to register."""
    await update.message.reply_text(
        "👋 Welcome to *E-DIM Copilot* — your personal assistant for your apartment building!\n\n"
        "I can answer questions about your building, upcoming events, and more.\n\n"
        "To get started, please register with /register.\n"
        "Already registered? Just send me any message and I'll help you.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ---------------------------------------------------------------------------
# /register  (multi-step ConversationHandler)
# ---------------------------------------------------------------------------


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Begin the registration conversation."""
    context.user_data[_REG_KEY] = {}
    await update.message.reply_text("What is your full name?")
    return REG_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[_REG_KEY]["full_name"] = update.message.text.strip()
    await update.message.reply_text("What is your apartment number?")
    return REG_APT


async def register_apt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[_REG_KEY]["apartment_number"] = update.message.text.strip()
    await update.message.reply_text("What is your building address?")
    return REG_ADDRESS


async def register_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Persist registration and finish the conversation."""
    reg = context.user_data[_REG_KEY]
    reg["building_address"] = update.message.text.strip()

    session_factory: sessionmaker[Session] = context.bot_data["session_factory"]
    with session_factory() as session:
        building = storage.get_or_create_building(session, reg["building_address"])
        storage.create_or_update_resident(
            session,
            telegram_id=update.effective_user.id,
            full_name=reg["full_name"],
            apartment_number=reg["apartment_number"],
            building=building,
        )
        session.commit()

    await update.message.reply_text(
        f"✅ Registered!\n\n"
        f"*Name:* {reg['full_name']}\n"
        f"*Apartment:* {reg['apartment_number']}\n"
        f"*Building:* {reg['building_address']}\n\n"
        "You can now chat with me about anything related to your building! 🏢",
        parse_mode=ParseMode.MARKDOWN,
    )
    context.user_data.pop(_REG_KEY, None)
    return ConversationHandler.END


async def register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop(_REG_KEY, None)
    await update.message.reply_text("Registration cancelled. Use /register to try again.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# /myinfo
# ---------------------------------------------------------------------------


async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the resident's stored profile."""
    session_factory: sessionmaker[Session] = context.bot_data["session_factory"]
    with session_factory() as session:
        resident = storage.get_resident_by_telegram_id(session, update.effective_user.id)
        if resident is None:
            await update.message.reply_text(
                "You are not registered yet. Use /register to set up your profile."
            )
            return
        await update.message.reply_text(
            f"👤 *Your profile*\n\n"
            f"*Name:* {resident.full_name}\n"
            f"*Apartment:* {resident.apartment_number}\n"
            f"*Building:* {resident.building.address}",
            parse_mode=ParseMode.MARKDOWN,
        )


# ---------------------------------------------------------------------------
# /events
# ---------------------------------------------------------------------------


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the latest building announcements for the resident."""
    session_factory: sessionmaker[Session] = context.bot_data["session_factory"]
    with session_factory() as session:
        resident = storage.get_resident_by_telegram_id(session, update.effective_user.id)
        if resident is None:
            await update.message.reply_text(
                "You are not registered yet. Use /register to set up your profile."
            )
            return
        announcements = storage.get_latest_announcements(session, resident.building_id)
        if not announcements:
            await update.message.reply_text("📭 No announcements for your building yet.")
            return
        lines = ["📢 *Latest announcements for your building:*\n"]
        for ann in announcements:
            date_str = ann.created_at.strftime("%Y-%m-%d") if ann.created_at else ""
            lines.append(f"📌 *{ann.title}* ({date_str})\n{ann.body}\n")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# Free-text AI chat
# ---------------------------------------------------------------------------


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any plain message by querying the AI assistant."""
    session_factory: sessionmaker[Session] = context.bot_data["session_factory"]
    openai_client: OpenAI = context.bot_data["openai_client"]
    model: str = context.bot_data["openai_model"]

    with session_factory() as session:
        resident = storage.get_resident_by_telegram_id(session, update.effective_user.id)
        if resident is None:
            await update.message.reply_text(
                "Please /register first so I can personalise my answers for you."
            )
            return

        announcements = storage.get_latest_announcements(session, resident.building_id)
        system_prompt = assistant.build_system_prompt(resident, announcements)

    history: list[dict[str, str]] = context.user_data.get(_HISTORY_KEY, [])

    try:
        reply = assistant.ask(
            client=openai_client,
            model=model,
            system_prompt=system_prompt,
            conversation_history=history,
            user_message=update.message.text,
        )
    except openai.OpenAIError as exc:
        logger.exception("OpenAI request failed: %s", exc)
        await update.message.reply_text(
            "Sorry, I'm having trouble reaching the AI service right now. Please try again later."
        )
        return

    # Update rolling conversation history
    history.append({"role": "user", "content": update.message.text})
    history.append({"role": "assistant", "content": reply})
    context.user_data[_HISTORY_KEY] = history[-(_MAX_HISTORY * 2):]

    await update.message.reply_text(reply)
