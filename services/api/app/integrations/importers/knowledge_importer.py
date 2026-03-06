
import os
import logging
from typing import List, Dict
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Organization

logger = logging.getLogger(__name__)

async def import_knowledge(provider_id: UUID, items: List[Dict]):
    """
    Import knowledge items into MongoDB 'knowledge' collection.
    Each item is expected to have: organization_id, type, search_text, payload, created_at.
    """
    if not items:
        return

    mongo_url = os.getenv("MONGO_URL")
    if not mongo_url:
        logger.error("MONGO_URL not set, skipping knowledge import")
        return

    # Resolve internal organization ID
    # Currently, we just pick the first organization for the provider.
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Organization).where(Organization.provider_id == provider_id)
        )
        organization = result.scalars().first()

    if not organization:
        logger.error(f"No organization found for provider {provider_id}, skipping knowledge import")
        return

    # Map external organization_id to internal one
    for item in items:
        item["organization_id"] = str(organization.id)

    mongo_client = AsyncIOMotorClient(mongo_url)
    try:
        mongo_db = mongo_client[os.getenv("MONGO_DB", "edim")]
        collection = mongo_db["knowledge"]

        await collection.delete_many({"organization_id": str(organization.id)})

        await collection.insert_many(items)
        logger.info(f"Imported {len(items)} knowledge items for organization: {organization.id}")
    finally:
        mongo_client.close()
