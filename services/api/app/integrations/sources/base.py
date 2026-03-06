from abc import ABC, abstractmethod
from typing import Any, List


class BaseSource(ABC):
    def __init__(self, config: dict):
        self.config = config

    async def load_buildings(self) -> List[Any]:
        return []

    async def load_units(self) -> List[Any]:
        return []

    async def load_residents(self) -> List[Any]:
        return []

    async def load_vehicles(self) -> List[Any]:
        return []

    async def load_unit_debts(self) -> List[Any]:
        return []

    async def load_knowledge(self) -> List[Any]:
        return []

    async def close(self):
        pass
