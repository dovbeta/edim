import os
import redis
from pymongo import MongoClient
import psycopg2

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.session import AsyncSessionLocal
from db.models import UserUnit, Unit, Building, Organization, User


class ContextManager:
    def __init__(self):
        self.pg = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

        self.mongo = MongoClient(os.getenv("MONGO_URL"))
        self.redis = redis.Redis(host=os.getenv("REDIS_HOST"), port=6379)

    async def build(self, user_id, message, chat_history=None):
        user = await self._get_user(user_id)
        properties = await self._get_user_properties(user_id)

        return {
            "user": user,
            "properties": properties,
        }

    async def _get_user(self, user_id) -> dict:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = res.scalars().first()

        if not user:
            return {"id": str(user_id), "exists": False}

        return {
            "id": str(user.id),
            "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "language": getattr(user, "language", "uk") or "uk",
            "exists": True,
        }

    async def _get_user_properties(self, user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserUnit)
                .where(UserUnit.user_id == user_id)
                .options(
                    selectinload(UserUnit.unit)
                    .selectinload(Unit.building)
                    .selectinload(Building.organization)
                )
            )

            links = result.scalars().all()

        properties = []

        for link in links:
            unit = link.unit
            if not unit:
                continue

            building = unit.building
            org = building.organization if building else None

            properties.append({
                "unit_id": str(unit.id),
                "unit_number": unit.personal_account,
                "unit_type": unit.unit_type,
                "floor": unit.floor,
                "section": unit.section,
                "rooms": unit.rooms,
                "area_total": unit.area_total,
                "role": link.role or "resident",
                "building": {
                    "id": str(building.id) if building else None,
                    "address": getattr(building, "address", None),
                },
                "organization": {
                    "id": str(org.id) if org else None,
                    "name": getattr(org, "name", None),
                }
            })

        return properties

