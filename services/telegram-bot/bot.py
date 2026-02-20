import os
import httpx
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# BASE URL API
BASE_URL = os.getenv("COPILOT_API_URL", "http://api:8000")

CHAT_URL = BASE_URL + "/chat"
CONTACT_URL = BASE_URL + "/chat/contact"

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user

    if not msg or not msg.text:
        return

    print("USER MSG:", msg.text)

    payload = {
        "channel": "telegram",
        "external_user_id": str(user.id),
        "message": msg.text,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
    }

    data = {}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(CHAT_URL, json=payload)

            print("API status:", r.status_code)
            print("API response:", r.text)

            if "application/json" in r.headers.get("content-type", ""):
                try:
                    data = r.json()
                except Exception:
                    data = {}
            else:
                print("Non-JSON response from API")

    except Exception as e:
        print("API request failed:", e)
        await msg.reply_text("⚠️ Copilot API недоступний")
        return

    # Phone request flow
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

    # Normal reply
    reply = (
        data.get("response")
        or data.get("answer")
        or data.get("text")
        or "⚠️ Copilot не надав відповіді"
    )

    await msg.reply_text(reply)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    tg_user = update.effective_user
    contact = msg.contact
    print("CONTACT:", contact)

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
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(CONTACT_URL, json=payload)

            print("CONTACT status:", r.status_code)
            print("CONTACT response:", r.text)

    except Exception as e:
        print("Contact send failed:", e)
        await msg.reply_text("⚠️ Помилка передачі номера")
        return

    await msg.reply_text(
        "Дякуємо! 🙌\n"
        "Ми перевіряємо інформацію про вашу нерухомість."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    print("Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()