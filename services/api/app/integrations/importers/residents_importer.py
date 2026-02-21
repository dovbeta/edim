from typing import List, Dict
from uuid import UUID

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Unit, User, UserUnit


async def import_residents(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        for item in items:
            # item should have "phone", "first_name", "last_name", "external_unit_id"
            phone = item.get("phone")
            if not phone:
                continue

            # Find or create user
            res = await session.execute(select(User).where(User.phone == phone))
            user = res.scalars().first()
            if not user:
                user = User(
                    phone=phone,
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                )
                session.add(user)
                await session.flush()

            # Find unit
            ext_unit_id = str(item.get("unit_id"))
            res = await session.execute(select(Unit).where(Unit.external_id == ext_unit_id))
            unit = res.scalars().first()
            if not unit:
                continue

            # Link user to unit if not linked
            res = await session.execute(
                select(UserUnit).where(
                    UserUnit.user_id == user.id,
                    Unit.id == unit.id
                )
            )
            # UserUnit has composite primary key (user_id, unit_id)
            user_unit = res.scalars().first()
            if not user_unit:
                user_unit = UserUnit(
                    user_id=user.id,
                    unit_id=unit.id,
                    role=item.get("role", "resident")
                )
                session.add(user_unit)

        await session.commit()
