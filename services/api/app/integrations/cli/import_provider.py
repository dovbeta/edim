import asyncio
import click
from uuid import UUID

from integrations.runner import run_provider_import


@click.command()
@click.option("--provider-id", required=True)
@click.option(
    "--include",
    multiple=True,
    type=click.Choice(["buildings", "units", "residents", "accruals"]),
    help="Specific entities to import. Can be specified multiple times.",
)
def import_provider(provider_id: str, include: tuple):
    include_list = list(include) if include else None
    asyncio.run(run_provider_import(UUID(provider_id), include=include_list))


if __name__ == "__main__":
    import_provider()