from typing import List, Dict
from uuid import UUID

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Unit, Building


def normalize_unit_type(raw: str | None) -> str:
    if not raw:
        return "apartment"
    v = str(raw).strip().lower()
    # Common Ukrainian/Russian labels from providers
    if "кварт" in v or v in {"apt", "apartment"}:
        return "apartment"
    if "парком" in v or "паркін" in v or "parking" in v:
        return "parking"
    if "комор" in v or "кладов" in v or "storage" in v:
        return "storage"
    return v


async def import_units(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        with session.no_autoflush:
            for i, item in enumerate(items):
                ext_b_id = item.get("building_external_id")
                number = item.get("number")

                if not ext_b_id or not number:
                    continue

                # ---------- find building ----------
                b_result = await session.execute(
                    select(Building).where(Building.external_id == str(ext_b_id))
                )
                building = b_result.scalars().first()

                if not building:
                    continue

                unit_type = normalize_unit_type(item.get("type", "apartment"))
                external_id = item.get("external_id")

                # ---------- find existing unit ----------
                existing_result = await session.execute(
                    select(Unit).where(
                        Unit.building_id == building.id,
                        Unit.number == str(number),
                        Unit.unit_type == unit_type,
                    )
                )
                unit = existing_result.scalars().first()

                # ---------- create ----------
                if not unit:
                    unit = Unit(
                        number=str(number),
                        building_id=building.id,
                        unit_type=unit_type,
                        external_id=str(external_id) if external_id else None,
                    )
                    session.add(unit)

                # ---------- update fields ----------
                unit.external_id = str(external_id) if external_id else unit.external_id

                unit.section = item.get("section")
                unit.floor = item.get("floor")

                unit.area_total = item.get("area_total")
                unit.area_living = item.get("area_living")
                unit.area_heating = item.get("area_heating")

                unit.rooms = item.get("rooms")
                unit.personal_account = item.get("personal_account")

                unit.residents_registered = item.get("residents_registered")
                unit.residents_living = item.get("residents_living")

                unit.is_debtor = item.get("is_debtor")

                if (i + 1) % 100 == 0:
                    await session.commit()

            await session.commit()