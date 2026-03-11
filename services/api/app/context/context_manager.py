from datetime import datetime
import zoneinfo
import os

import redis
from pymongo import MongoClient
import psycopg2

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models.user_organization import UserOrganization
from db.session import AsyncSessionLocal
from db.models import UserUnit, Unit, Building, Organization, User, Vehicle


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
        vehicles = await self._get_user_vehicles(user_id)
        org_roles = await self._get_user_org_roles(user_id)
        scope = self._build_scope(properties, org_roles)

        return {
            "time": self._get_time_context(),
            "user": user,
            "properties": properties,
            "vehicles": vehicles,
            "org_roles": org_roles,
            "scope": scope,
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
                "debt_total": unit.debt_total,
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

    async def _get_user_vehicles(self, user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Vehicle).where(Vehicle.user_id == user_id)
            )
            vehicles = result.scalars().all()

        return [
            {
                "id": str(v.id),
                "model": v.model,
                "license_plate": v.license_plate,
            }
            for v in vehicles
        ]

    async def _get_user_org_roles(self, user_id):
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(UserOrganization)
                .where(UserOrganization.user_id == user_id)
                .options(
                    selectinload(UserOrganization.organization)
                )
            )
            rows = res.scalars().all()

        roles = []

        for r in rows:
            org = r.organization
            roles.append({
                "organization_id": str(r.organization_id),
                "organization_name": getattr(org, "name", None) if org else None,
                "role": r.role,
            })

        return roles

    @staticmethod
    def _get_time_context():
        now = datetime.now(zoneinfo.ZoneInfo("Europe/Kyiv"))

        return {
            "now": now.isoformat(),
            "today": str(now.date()),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "timezone": "Europe/Kyiv"
        }

    def _build_scope(self, properties, org_roles):
        org_ids = set()
        building_ids = set()
        unit_ids = set()

        for p in properties:
            if p["organization"]["id"]:
                org_ids.add(p["organization"]["id"])

            if p["building"]["id"]:
                building_ids.add(p["building"]["id"])

            unit_ids.add(p["unit_id"])

        for r in org_roles:
            org_ids.add(r["organization_id"])

        return {
            "organization_ids": list(org_ids),
            "building_ids": list(building_ids),
            "unit_ids": list(unit_ids),
        }

