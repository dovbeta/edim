from typing import List, Dict
from uuid import UUID
import math
import logging

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Unit, User, UserUnit, Building, Organization

from .units_importer import normalize_unit_type

logger = logging.getLogger(__name__)


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
            total = len(items or [])
            created_users = 0
            updated_users = 0
            skipped_no_phone = 0
            skipped_no_unit_number = 0
            unit_not_found = 0
            links_created = 0
            links_existing = 0

            bad_unit_examples = []

            for i, item in enumerate(items or []):

                phone = clean_str(item.get("phone"))
                if not phone:
                    skipped_no_phone += 1
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
                    created_users += 1
                else:
                    if not user.email and email:
                        user.email = email
                        updated_users += 1

                # --- unit ---
                unit_number = clean_str(item.get("unit_number"))
                if not unit_number:
                    skipped_no_unit_number += 1
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
                    unit_not_found += 1
                    if len(bad_unit_examples) < 5:
                        bad_unit_examples.append(
                            {
                                "phone": phone,
                                "unit_number": unit_number,
                                "unit_type": unit_type_raw,
                                "normalized_unit_type": unit_type,
                                "section": section,
                            }
                        )
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
                    links_created += 1
                else:
                    links_existing += 1

                if (i + 1) % 100 == 0:
                    await session.commit()
                    logger.info(
                        "import_residents progress provider_id=%s i=%s/%s created_users=%s links_created=%s unit_not_found=%s",
                        provider_id,
                        i + 1,
                        total,
                        created_users,
                        links_created,
                        unit_not_found,
                    )

            await session.commit()

            logger.info(
                "import_residents done provider_id=%s total=%s created_users=%s updated_users=%s skipped_no_phone=%s skipped_no_unit_number=%s unit_not_found=%s links_created=%s links_existing=%s",
                provider_id,
                total,
                created_users,
                updated_users,
                skipped_no_phone,
                skipped_no_unit_number,
                unit_not_found,
                links_created,
                links_existing,
            )
            if bad_unit_examples:
                logger.warning("import_residents unit_not_found examples=%s", bad_unit_examples)