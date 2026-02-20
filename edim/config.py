"""Configuration loaded from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    def __init__(
        self,
        telegram_bot_token: str | None = None,
        openai_api_key: str | None = None,
        database_url: str | None = None,
        openai_model: str | None = None,
    ) -> None:
        self.TELEGRAM_BOT_TOKEN: str = telegram_bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.OPENAI_API_KEY: str = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.DATABASE_URL: str = database_url or os.environ.get("DATABASE_URL", "sqlite:///edim.db")
        self.OPENAI_MODEL: str = openai_model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def validate(self) -> None:
        """Raise if required configuration is missing."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
