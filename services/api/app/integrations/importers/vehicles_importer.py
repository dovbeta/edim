import math
from typing import List, Dict

from db.models import User, Vehicle
from db.session import AsyncSessionLocal
from sqlalchemy import select


def clean_str(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    return s if s else None

async def import_vehicles(items: List[Dict]):
    async with AsyncSessionLocal() as session:
        for item in items:

            phone = clean_str(item.get("phone"))
            if not phone:
                continue

            model = clean_str(item.get("model"))
            plate = clean_str(item.get("license_plate"))

            if not model and not plate:
                continue

            # --- user ---
            res = await session.execute(
                select(User).where(User.phone == phone)
            )
            user = res.scalars().first()
            if not user:
                continue

            # --- check duplicate ---
            res = await session.execute(
                select(Vehicle).where(
                    Vehicle.user_id == user.id,
                    Vehicle.license_plate == plate,
                )
            )
            exists = res.scalars().first()

            if exists:
                continue

            session.add(
                Vehicle(
                    user_id=user.id,
                    model=model,
                    license_plate=plate,
                )
            )

        await session.commit()