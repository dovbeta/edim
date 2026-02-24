import os
import asyncio
import httpx
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters, CommandHandler,
)
from telegram.constants import ChatAction

BASE_URL = os.getenv("COPILOT_API_URL", "http://api:8000")

CHAT_URL = BASE_URL + "/chat"
CONTACT_URL = BASE_URL + "/chat/contact"

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user

    if not msg:
        return

    payload = {
        "channel": "telegram",
        "external_user_id": str(user.id),
        "message": "/start",
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
    }

    # швидко питаємо backend: чи потрібен телефон
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(CHAT_URL, json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        print("START API failed:", e)
        await msg.reply_text("👋 Вітаємо в E-Dim Copilot!")
        return

    if data.get("need_phone"):
        button = KeyboardButton(
            text="📱 Поділитися номером",
            request_contact=True
        )
        kb = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

        await msg.reply_text(
            data.get(
                "text",
                "👋 Вітаємо!\nПоділіться номером телефону 📱"
            ),
            reply_markup=kb
        )
        return

    # якщо вже відомий
    await msg.reply_text("👋 Вітаємо в E-Dim Copilot! Чим можу допомогти?")

# =====================================================
# TYPING INDICATOR LOOP
# =====================================================

async def typing_loop(chat):
    try:
        while True:
            await chat.send_action("typing")
            await asyncio.sleep(4)  # Telegram typing живе ~5 сек
    except asyncio.CancelledError:
        pass


# =====================================================
# BACKGROUND COPILOT CALL
# =====================================================

async def fetch_and_reply(msg, payload):
    typing_task = asyncio.create_task(typing_loop(msg.chat))

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(CHAT_URL, json=payload)
            r.raise_for_status()

            data = (
                r.json()
                if "application/json" in r.headers.get("content-type", "")
                else {}
            )

    except Exception as e:
        print("API request failed:", e)
        typing_task.cancel()
        await msg.reply_text("⚠️ Copilot тимчасово недоступний")
        return

    typing_task.cancel()

    # 📱 API просить телефон
    if data.get("need_phone"):
        button = KeyboardButton(
            text="📱 Поділитися номером",
            request_contact=True
        )
        kb = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

        await msg.reply_text(
            data.get("text", "Будь ласка, поділіться номером"),
            reply_markup=kb
        )
        return

    reply = (
        data.get("text")
        or data.get("answer")
        or data.get("response")
        or "⚠️ Copilot не надав відповіді"
    )

    await msg.reply_text(reply)


# =====================================================
# TEXT MESSAGE
# =====================================================

def is_bot_mentioned(msg) -> bool:
    if not msg or not msg.text:
        return False

    text = msg.text

    # 1️⃣ приват — реагуємо на все
    if msg.chat.type == "private":
        return True

    # 2️⃣ !
    if text.strip().startswith("!"):
        return True

    return False

def clean_message(text: str) -> str:
    if not text:
        return text

    if text.startswith("!"):
        text = text[1:].strip()

    return text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user

    if not is_bot_mentioned(msg):
        return

    clean_text = clean_message(msg.text)

    payload = {
        "channel": "telegram",
        "external_user_id": str(user.id),
        "message": clean_text,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
    }

    # 🚀 фоновий виклик Copilot (з typing)
    context.application.create_task(
        fetch_and_reply(msg, payload)
    )


# =====================================================
# CONTACT
# =====================================================

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    tg_user = update.effective_user
    contact = msg.contact

    if not contact:
        return

    payload = {
        "channel": "telegram",
        "external_user_id": str(tg_user.id),
        "phone": contact.phone_number,
        "first_name": tg_user.first_name,
        "last_name": tg_user.last_name,
        "username": tg_user.username,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(CONTACT_URL, json=payload)
            r.raise_for_status()

            data = (
                r.json()
                if "application/json" in r.headers.get("content-type", "")
                else {}
            )

    except Exception as e:
        print("Contact send failed:", e)
        await msg.reply_text("⚠️ Помилка передачі номера")
        return

    reply = data.get("text") or "Дякуємо! 🙌"

    await msg.reply_text(
        reply,
        reply_markup=ReplyKeyboardRemove()
    )


# =====================================================
# BOOT
# =====================================================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(CommandHandler("start", handle_start))

    print("Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()