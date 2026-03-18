from typing import List, Dict
from uuid import UUID
import math

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Unit, User, UserUnit, Building, Organization

from .units_importer import normalize_unit_type


def clean_str(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    return s if s else None


async def import_residents(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        with session.no_autoflush:
            for i, item in enumerate(items):

                phone = clean_str(item.get("phone"))
                if not phone:
                    continue

                first_name = clean_str(item.get("first_name"))
                last_name = clean_str(item.get("last_name"))
                middle_name = clean_str(item.get("middle_name"))
                email = clean_str(item.get("email"))

                # --- user ---
                res = await session.execute(
                    select(User).where(User.phone == phone)
                )
                user = res.scalars().first()

                if not user:
                    user = User(
                        phone=phone,
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middle_name,
                        email=email,
                    )
                    session.add(user)
                    await session.flush()  # отримати user.id
                else:
                    if not user.email and email:
                        user.email = email

                # --- unit ---
                unit_number = clean_str(item.get("unit_number"))
                if not unit_number:
                    continue
                unit_type_raw = clean_str(item.get("unit_type"))
                unit_type = normalize_unit_type(unit_type_raw) if unit_type_raw else None
                section = clean_str(item.get("section"))

                conditions = [
                    Unit.number == unit_number,
                    Organization.provider_id == provider_id,
                ]
                if unit_type:
                    conditions.append(Unit.unit_type == unit_type)
                if section:
                    conditions.append(Unit.section == section)

                res = await session.execute(
                    select(Unit)
                    .join(Building, Unit.building_id == Building.id)
                    .join(Organization, Building.organization_id == Organization.id)
                    .where(*conditions)
                )
                unit = res.scalars().first()
                if not unit:
                    continue

                # --- link ---
                res = await session.execute(
                    select(UserUnit).where(
                        UserUnit.user_id == user.id,
                        UserUnit.unit_id == unit.id,
                    )
                )
                link = res.scalars().first()

                if not link:
                    session.add(
                        UserUnit(
                            user_id=user.id,
                            unit_id=unit.id,
                            role=clean_str(item.get("role")) or "resident",
                        )
                    )

                if (i + 1) % 100 == 0:
                    await session.commit()

            await session.commit()