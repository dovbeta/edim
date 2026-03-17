from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from uuid import UUID

from sqlalchemy import select

from db.session import AsyncSessionLocal
from db.models import Unit, Building, Organization


async def import_debts(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        with session.no_autoflush:
            for i, item in enumerate(items):
                pa = item.get("personal_account")
                debt = item.get("debt_total")

                if not pa:
                    continue

                # Match units only within buildings that belong to organizations
                # served by this provider. This prevents overwriting debts for
                # units of other organizations that may reuse the same personal
                # account number.
                res = await session.execute(
                    select(Unit)
                    .join(Building, Unit.building_id == Building.id)
                    .join(Organization, Building.organization_id == Organization.id)
                    .where(
                        Unit.personal_account == str(pa),
                        Organization.provider_id == provider_id,
                    )
                )
                unit = res.scalars().first()

                if not unit:
                    continue

                value = Decimal(str(debt or 0)).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                unit.debt_total = value

                if (i + 1) % 100 == 0:
                    await session.commit()
            
            await session.commit()
