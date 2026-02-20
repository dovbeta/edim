"""E-DIM Copilot — Telegram bot entry point."""
import logging

from openai import OpenAI
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from edim.config import Config
from edim.handlers import (
    REG_ADDRESS,
    REG_APT,
    REG_NAME,
    chat,
    events,
    myinfo,
    register_address,
    register_apt,
    register_cancel,
    register_name,
    register_start,
    start,
)
from edim.storage import create_session_factory

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_application(config: Config | None = None) -> Application:
    """Build and return the configured Telegram Application."""
    if config is None:
        config = Config()

    config.validate()

    session_factory = create_session_factory(config.DATABASE_URL)
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Shared state available to all handlers
    app.bot_data["session_factory"] = session_factory
    app.bot_data["openai_client"] = openai_client
    app.bot_data["openai_model"] = config.OPENAI_MODEL

    # /register multi-step conversation
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REG_APT: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_apt)],
            REG_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_address)],
        },
        fallbacks=[CommandHandler("cancel", register_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(registration_handler)
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    return app


def main() -> None:
    """Start the bot with long-polling."""
    app = build_application()
    logger.info("E-DIM Copilot is running…")
    app.run_polling()


if __name__ == "__main__":
    main()
