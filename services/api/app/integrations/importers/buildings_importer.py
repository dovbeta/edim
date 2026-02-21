from typing import List, Dict
from uuid import UUID

from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Building, Organization


async def import_buildings(provider_id: UUID, items: List[Dict]):
    async with AsyncSessionLocal() as session:
        # For now, we assume there's at least one organization for this provider.
        # In a real scenario, we might want to map external_org_id to organization.
        result = await session.execute(
            select(Organization).where(Organization.provider_id == provider_id)
        )
        organization = result.scalars().first()

        if not organization:
            # Fallback or error
            # TODO: create default organization if not exists?
            return

        for b in items:
            # Check if building already exists
            existing_result = await session.execute(
                select(Building).where(
                    Building.organization_id == organization.id,
                    Building.external_id == str(b.get("id"))
                )
            )
            building = existing_result.scalars().first()

            if building:
                building.name = b.get("name")
            else:
                building = Building(
                    name=b.get("name"),
                    organization_id=organization.id,
                    external_id=str(b.get("id")),
                )
                session.add(building)

        await session.commit()