import logging
from datetime import datetime
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Provider, Organization

from .provider_loader import load_provider_source
from .importers.units_importer import import_units
from .importers.buildings_importer import import_buildings
from .importers.residents_importer import import_residents
from .importers.vehicles_importer import import_vehicles
from .importers.debts_importer import import_debts
from .importers.knowledge_importer import import_knowledge
from .knowledge_vectorizer import vectorize_knowledge

logger = logging.getLogger(__name__)

async def run_provider_import(provider_id, include=None):
    if include is None:
        include = ["buildings", "units", "residents", "vehicles", "debts", "knowledge"]

    async with AsyncSessionLocal() as session:
        provider = await session.get(Provider, provider_id)
        if not provider:
            logger.error(f"Provider {provider_id} not found")
            return

    source = load_provider_source(provider)

    try:
        logger.info(f"Starting import for provider {provider.name} (include: {include})")

        if "buildings" in include:
            buildings = await source.load_buildings()
            await import_buildings(provider.id, buildings)

        if "units" in include:
            units = await source.load_units()
            await import_units(provider.id, units)

        if "residents" in include:
            residents = await source.load_residents()
            await import_residents(provider.id, residents)

        if "vehicles" in include:
            vehicles = await source.load_vehicles()
            await import_vehicles(vehicles)

        if "debts" in include:
            try:
                debts = await source.load_unit_debts()
                await import_debts(provider.id, debts)
                logger.info(f"Imported {len(debts)} unit debts")
            except AttributeError:
                logger.info("Source does not support load_unit_debts, skipping debts import")

        if "knowledge" in include:
            try:
                knowledge = await (source.
                                   load_knowledge())
                await import_knowledge(provider.id, knowledge)
                logger.info(f"Imported {len(knowledge)} knowledge items")
                
                # Auto-vectorize imported knowledge
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(Organization).where(Organization.provider_id == provider_id)
                    )
                    organization = result.scalars().first()
                    if organization:
                        await vectorize_knowledge(str(organization.id))
            except AttributeError:
                logger.info("Source does not support load_knowledge, skipping knowledge import")

        async with AsyncSessionLocal() as session:
            # Re-fetch or use session.merge if needed, but we just want to update last_import_at
            provider = await session.get(Provider, provider_id)
            provider.last_import_at = datetime.utcnow()
            await session.commit()

        logger.info(f"Import finished for provider {provider.name}")
    except Exception as e:
        logger.exception(f"Error importing from provider {provider.name}: {e}")
    finally:
        await source.close()
