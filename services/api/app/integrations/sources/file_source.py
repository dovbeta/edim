from pathlib import Path
from .base import BaseSource


class FileSource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.path = Path(config.get("path", ""))

    async def load_units(self):
        # TODO: CSV/Excel parser
        return []
