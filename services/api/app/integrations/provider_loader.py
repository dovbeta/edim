from db.models import Provider

from .sources.api_source import APISource
from .sources.file_source import FileSource
from .sources.gdrive_source import GDriveSource
from .sources.dah_api_source import DahAPISource


def load_provider_source(provider: Provider):
    cfg = provider.integration_config or {}

    if provider.integration_type == "api":
        cfg = provider.integration_config or {}

        if cfg.get("provider") == "dah":
            return DahAPISource(cfg)

        return APISource(cfg)

    if provider.integration_type == "file":
        source_type = cfg.get("source")

        if source_type == "gdrive":
            return GDriveSource(cfg)

        return FileSource(cfg)

    raise ValueError(f"Unknown integration_type {provider.integration_type}")