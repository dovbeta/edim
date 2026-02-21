from typing import List, Dict
from uuid import UUID

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Unit, Building


async def import_units(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        for item in items:
            ext_b_id = str(item.get("building_external_id"))

            if not ext_b_id:
                continue

            b_result = await session.execute(
                select(Building).where(Building.external_id == ext_b_id)
            )
            building = b_result.scalars().first()

            if not building:
                continue

            number = str(item.get("number"))
            unit_type = item.get("type", "apartment")
            external_id = str(item.get("external_id"))

            existing_result = await session.execute(
                select(Unit).where(
                    Unit.building_id == building.id,
                    Unit.number == number,
                    Unit.unit_type == unit_type
                )
            )
            unit = existing_result.scalars().first()

            if unit:
                unit.external_id = external_id
            else:
                session.add(
                    Unit(
                        number=number,
                        building_id=building.id,
                        unit_type=unit_type,
                        external_id=external_id,
                    )
                )

        await session.commit()