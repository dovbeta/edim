import io
import json
import pandas as pd
import httpx
import re
import zipfile
import logging
from typing import List, Dict
from .api_source import APISource
from datetime import datetime
from utils.gdrive import GoogleDriveClient

logger = logging.getLogger(__name__)

def parse_premises(text: str):
    if text is None:
        return None, None, None

    # Excel may provide NaN as float; treat as empty.
    if isinstance(text, float):
        # NaN check without importing math
        if text != text:
            return None, None, None

    if not str(text).strip():
        return None, None, None

    text = str(text).strip()

    # optional section
    section_match = re.search(r"Під.?їзд\s*(\d+)", text, re.IGNORECASE)
    section = section_match.group(1) if section_match else None

    # unit type + number (last word before number is type)
    # Supports suffix after digits, e.g. "Квартира 160а", "110A"
    m = re.search(
        r"([^\d]+?)\s*(\d+)\s*([A-Za-zА-Яа-яІіЇїЄєҐґ])?\s*$",
        text,
    )

    if not m:
        return section, None, None

    unit_type = m.group(1).strip().lower().strip(" ,.-")
    number = m.group(2)
    suffix = (m.group(3) or "").strip()

    # Convert Latin lookalike suffix letters to Ukrainian Cyrillic
    # so "160A" matches "160а" in DB.
    _lat_to_cyr = str.maketrans({
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "I": "І",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "Y": "У",
        "a": "а",
        "b": "в",
        "c": "с",
        "e": "е",
        "h": "н",
        "i": "і",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "t": "т",
        "x": "х",
        "y": "у",
    })
    if suffix:
        suffix = str(suffix).translate(_lat_to_cyr).lower()
    number = f"{number}{suffix}" if suffix else number

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
        total_rows = len(df)
        parsed_ok = 0
        missing_premises = 0
        parse_failed = 0
        bad_examples = []

        for _, row in df.iterrows():
            premises = row.get("Приміщення")

            section, unit_type, unit_number = parse_premises(premises)
            if premises is None or (isinstance(premises, float) and premises != premises):
                missing_premises += 1

            if section is None and unit_type is None and unit_number is None:
                parse_failed += 1
                if len(bad_examples) < 5:
                    bad_examples.append({"premises": str(premises)[:80] if premises is not None else None})

            full_name = row.get("ПІП")
            last_name, first_name, middle_name = split_full_name(full_name)

            if unit_number:
                parsed_ok += 1

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

        logger.info(
            "load_residents: total_rows=%s parsed_ok=%s missing_premises=%s parse_failed=%s",
            total_rows,
            parsed_ok,
            missing_premises,
            parse_failed,
        )
        if bad_examples:
            logger.warning("load_residents bad_examples=%s", bad_examples)

        return residents

    async def load_vehicles(self) -> List[Dict]:
        file_url = self.config.get("vehicles_file_url")
        if not file_url:
            return []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(file_url)
            r.raise_for_status()

        content = r.content or b""
        content_type = r.headers.get("content-type", "")

        def _looks_like_html(b: bytes) -> bool:
            head = b[:256].lstrip().lower()
            return head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<html" in head

        def _looks_like_xlsx_zip(b: bytes) -> bool:
            # XLSX is a zip; zip files start with PK
            return b[:2] == b"PK"

        def _looks_like_xls_ole(b: bytes) -> bool:
            # OLE2 compound document header
            return b[:8] == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"

        df = None
        try:
            if _looks_like_xlsx_zip(content):
                df = pd.read_excel(io.BytesIO(content), engine="openpyxl", header=2)
            else:
                # try auto engine (may work if xlrd is installed for .xls)
                df = pd.read_excel(io.BytesIO(content), header=2)
        except zipfile.BadZipFile:
            # Not an XLSX zip, try xls engine if available
            if _looks_like_xls_ole(content):
                try:
                    df = pd.read_excel(io.BytesIO(content), engine="xlrd", header=2)
                except Exception as e:
                    raise ValueError(
                        "Vehicles file looks like old .xls, but required engine is missing. "
                        "Provide .xlsx file or install xlrd."
                    ) from e
            elif _looks_like_html(content):
                raise ValueError(
                    "Vehicles file URL returned HTML instead of an Excel file. "
                    "If this is a Google Drive share link, use a direct download/export link."
                )
            else:
                raise
        except ValueError:
            # Some providers return CSV
            try:
                df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
            except Exception:
                logger.exception(
                    "Failed to parse vehicles file. content_type=%s size=%s url=%s",
                    content_type,
                    len(content),
                    file_url,
                )
                raise

        if df is None:
            raise ValueError("Vehicles file could not be parsed")

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