import io
import pandas as pd
import httpx
import re
from typing import List, Dict
from .api_source import APISource

def parse_premises(text: str):
    if not text:
        return None, None, None

    # Під’їзд 11, Квартира 237
    m = re.search(r"Під.?їзд\s*(\d+).*,\s*(\w+)\s*([\w\d]+)", text)

    if not m:
        return None, None, None

    section = m.group(1)
    raw_type = m.group(2).lower()
    number = m.group(3)

    type_map = {
        "квартира": "apartment",
        "офіс": "commercial",
        "комора": "storage",
        "паркінг": "parking",
        "гараж": "garage",
    }

    unit_type = type_map.get(raw_type, "apartment")

    return section, unit_type, number

def split_full_name(full_name: str):
    if not full_name:
        return None, None, None

    name = str(full_name).strip()

    # прибрати сміття типу "? "
    name = name.lstrip("?").strip()

    parts = [p for p in name.split() if p]

    last_name = None
    first_name = None
    middle_name = None

    if len(parts) == 1:
        first_name = parts[0]

    elif len(parts) == 2:
        last_name, first_name = parts

    elif len(parts) >= 3:
        last_name = parts[0]
        first_name = parts[1]
        middle_name = " ".join(parts[2:])

    return last_name, first_name, middle_name

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
                    "type": ad.get("apartmentType"),
                    "area_total": ad.get("size"),
                    "floor": ad.get("floor"),
                    "section": ad.get("sectionNumber"),
                    "rooms": ad.get("rooms"),
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

    async def load_residents(self) -> List[Dict]:
        file_url = self.config.get("residents_file_url")
        if not file_url:
            return []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(file_url)
            r.raise_for_status()

        try:
            df = pd.read_excel(
                io.BytesIO(r.content),
                engine="openpyxl",
                header=2,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to parse Excel file from {file_url}: {e}"
            )

        residents: List[Dict] = []

        for _, row in df.iterrows():
            premises = row.get("Приміщення")

            section, unit_type, unit_number = parse_premises(premises)
            full_name = row.get("ПІП")
            last_name, first_name, middle_name = split_full_name(full_name)

            residents.append(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "middle_name": middle_name,
                    "phone": row.get("Телефон"),
                    "email": row.get("E-mail"),
                    "role": row.get("Частка"),
                    "unit_number": unit_number,
                    "unit_type": unit_type,
                    "section": section,
                }
            )

        return residents