import httpx
from typing import Any, List
from .base import BaseSource


class APISource(BaseSource):
    def __init__(self, config: dict):
        super().__init__(config)

        self.base_url = config.get("base_url")
        self.token = config.get("token")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            },
            timeout=30,
        )

    async def close(self):
        await self.client.aclose()

    async def get(self, path: str):
        r = await self.client.get(path)
        r.raise_for_status()
        return r.json()

    async def load_buildings(self) -> List[Any]:
        return await self.get("/buildings")

    async def load_units(self) -> List[Any]:
        return await self.get("/units")

    async def load_residents(self) -> List[Any]:
        return await self.get("/residents")