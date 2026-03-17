from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Lightweight application configuration loaded from environment."""

    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "edim")


settings = Settings()

