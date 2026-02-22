import logging
from datetime import datetime
from db.session import AsyncSessionLocal
from db.models import Provider

from .provider_loader import load_provider_source
from .importers.units_importer import import_units
from .importers.buildings_importer import import_buildings
from .importers.residents_importer import import_residents
from .importers.vehicles_importer import import_vehicles

logger = logging.getLogger(__name__)

async def run_provider_import(provider_id, include=None):
    if include is None:
        include = ["buildings", "units", "residents", "vehicles", "accruals"]

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

        if "accruals" in include:
            # TODO: implement accruals importer
            logger.info("Accruals import requested but not yet implemented")

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
