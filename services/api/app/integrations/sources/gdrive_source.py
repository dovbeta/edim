from .base import BaseSource


class GDriveSource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)
        self.folder_id = config.get("folder_id")
        self.pattern = config.get("pattern")

    async def load_units(self):
        # TODO: download latest file from GDrive
        return []
