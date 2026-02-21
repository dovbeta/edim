import asyncio

from app.db.session import AsyncSessionLocal
from app.db.models import Provider
from app.integrations.runner import run_provider_import


async def main():
    async with AsyncSessionLocal() as session:
        # Note: Using select(Provider) is more idiomatic with AsyncSessionLocal
        from sqlalchemy import select
        result = await session.execute(select(Provider))
        providers = result.scalars().all()

    for p in providers:
        await run_provider_import(p.id)


if __name__ == "__main__":
    asyncio.run(main())