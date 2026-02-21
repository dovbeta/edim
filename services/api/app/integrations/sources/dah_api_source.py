from typing import List, Dict
from .api_source import APISource


class DahAPISource(APISource):

    async def load_units(self) -> List[Dict]:
        data = await self.get("/v1/dictionary/apartments")

        units: List[Dict] = []
        buildings: Dict[str, Dict] = {}

        for a in data:
            ad = a.get("apartmentData") or {}

            building_num = ad.get("buildingNumber")
            apartment_num = ad.get("apartmentNumber")

            if building_num:
                buildings[building_num] = {
                    "external_id": str(building_num),
                    "name": f"Будинок {building_num}",
                }

            units.append(
                {
                    "external_id": a.get("id"),
                    "number": apartment_num,
                    "type": "apartment",
                    "area": ad.get("size"),
                    "floor": ad.get("floor"),
                    "section": ad.get("sectionNumber"),
                    "building_external_id": str(building_num) if building_num else None,
                    "personal_account": a.get("personalAccountNumber"),
                }
            )

        self._buildings_cache = list(buildings.values())
        return units

    async def load_buildings(self) -> List[Dict]:
        if hasattr(self, "_buildings_cache"):
            return self._buildings_cache

        await self.load_units()
        return self._buildings_cache