import io
import json
import pandas as pd
import httpx
import re
import zipfile
from typing import List, Dict
from .api_source import APISource
from datetime import datetime
from utils.gdrive import GoogleDriveClient

def parse_premises(text: str):
    if not text:
        return None, None, None

    text = text.strip()

    # optional section
    section_match = re.search(r"Під.?їзд\s*(\d+)", text, re.IGNORECASE)
    section = section_match.group(1) if section_match else None

    # unit type + number (last word before number is type)
    m = re.search(r"([^\d]+?)\s*(\d+)\s*$", text)

    if not m:
        return section, None, None

    unit_type = m.group(1).strip().lower()
    number = m.group(2)

    # прибираємо "Під’їзд X," якщо він є
    unit_type = re.sub(r"Під.?їзд\s*\d+,\s*", "", unit_type, flags=re.IGNORECASE)

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

    async def load_vehicles(self) -> List[Dict]:
        file_url = self.config.get("vehicles_file_url")
        if not file_url:
            return []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(file_url)
            r.raise_for_status()

        df = pd.read_excel(
            io.BytesIO(r.content),
            engine="openpyxl",
            header=2,
        )

        df["ПІП"] = df["ПІП"].ffill()
        df["Телефон"] = df["Телефон"].ffill()

        vehicles: List[Dict] = []

        for _, row in df.iterrows():
            vehicles.append(
                {
                    "full_name": row.get("ПІП"),
                    "phone": row.get("Телефон"),
                    "model": row.get("Модель"),
                    "license_plate": row.get("Номер"),
                }
            )

        return vehicles

    async def load_unit_debts(self) -> List[Dict]:
        folder_id = self.config.get("debts_folder_id")
        service_account_info = self.config.get("google_service_account_json")

        if not folder_id or not service_account_info:
            return []


        gdrive = GoogleDriveClient(service_account_info)
        files = gdrive.list_files(folder_id, q="name contains '.zip'")

        if not files:
            return []

        # List is already sorted by createdTime desc
        latest_file = files[0]
        content = gdrive.download_file(latest_file["id"])


        z = zipfile.ZipFile(io.BytesIO(content))
        # Find excel file in zip
        excel_file = None
        for name in z.namelist():
            if name.endswith(".xlsx") or name.endswith(".xls"):
                excel_file = name
                break

        if not excel_file:
            return []

        with z.open(excel_file) as f:
            df = pd.read_excel(f, engine="openpyxl")

        # 🔹 нормалізуємо назви колонок
        df.columns = [str(c).strip() for c in df.columns]

        # 🔹 очікувані колонки
        if "LS" not in df.columns or "SUM" not in df.columns:
            raise ValueError("Debt file must contain LS and SUM columns")

        # 🔹 приводимо типи
        df["LS"] = df["LS"].astype(str)
        df["SUM"] = pd.to_numeric(df["SUM"], errors="coerce").fillna(0)

        # 🔹 агрегуємо борг по особовому рахунку
        agg = (
            df.groupby("LS", as_index=False)["SUM"]
            .sum()
            .rename(columns={"LS": "personal_account", "SUM": "debt_total"})
        )

        # 🔹 конвертуємо в список dict
        debts = agg.to_dict(orient="records")

        return debts

    async def load_knowledge(self) -> List[Dict]:
        folder_id = self.config.get("knowledge_folder_id")
        service_account_info = self.config.get("google_service_account_json")

        if not folder_id or not service_account_info:
            return []

        gdrive = GoogleDriveClient(service_account_info)
        q = "name = 'knowledge_base.json'"
        files = gdrive.list_files(folder_id, q=q)

        if not files:
            return []

        # Get the latest knowledge file
        latest_file = files[0]
        content = gdrive.download_file(latest_file["id"])
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]