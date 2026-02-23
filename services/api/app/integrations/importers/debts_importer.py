from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from uuid import UUID
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Unit


async def import_debts(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        for item in items:
            pa = item.get("personal_account")
            debt = item.get("debt_total")

            if not pa:
                continue

            res = await session.execute(
                select(Unit).where(Unit.personal_account == str(pa))
            )
            unit = res.scalars().first()

            if not unit:
                continue

            value = Decimal(str(debt or 0)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            unit.debt_total = value

        await session.commit()
