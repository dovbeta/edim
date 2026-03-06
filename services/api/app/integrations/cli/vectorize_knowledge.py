import asyncio
import click
import logging
import sys
import os

# Add services/api/app to sys.path to allow imports to work
sys.path.append(os.path.join(os.getcwd(), "services", "api", "app"))

from integrations.knowledge_vectorizer import vectorize_knowledge

@click.command()
@click.option("--org-id", required=True, help="Organization UUID to vectorize knowledge for")
def vectorize_cmd(org_id: str):
    logging.basicConfig(level=logging.INFO)
    asyncio.run(vectorize_knowledge(org_id))

if __name__ == "__main__":
    vectorize_cmd()
