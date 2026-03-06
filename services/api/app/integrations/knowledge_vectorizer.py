
import os
import logging
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from llm.openai_embed import OpenAIEmbeddingClient

logger = logging.getLogger(__name__)

BATCH_SIZE = 50

async def vectorize_knowledge(organization_id: str):
    """
    Service to vectorize knowledge documents for a specific organization using Gemini.
    """
    mongo_url = os.getenv("MONGO_URL")
    if not mongo_url:
        logger.error("MONGO_URL not set, skipping vectorization")
        return

    mongo_client = AsyncIOMotorClient(mongo_url)
    try:
        mongo_db = mongo_client[os.getenv("MONGO_DB", "edim")]
        collection = mongo_db["knowledge"]
        
        embedding_client = OpenAIEmbeddingClient()

        # 1. Extraction: Query for documents missing the 'embedding' field for the specific organization
        query = {
            "organization_id": organization_id,
            "embedding": {"$exists": False}
        }
        
        cursor = collection.find(query)
        batch: List[Dict[str, Any]] = []

        async for doc in cursor:
            batch.append(doc)

            if len(batch) >= BATCH_SIZE:
                await _process_batch(collection, embedding_client, batch)
                batch = []

        if batch:
            await _process_batch(collection, embedding_client, batch)

        logger.info(f"Vectorization completed for organization {organization_id}")

    finally:
        mongo_client.close()

async def _process_batch(collection, embedding_client : OpenAIEmbeddingClient, batch: List[Dict[str, Any]]):
    try:
        # Filter documents with non-empty search_text
        valid_docs = [doc for doc in batch if doc.get("search_text", "").strip()]
        if not valid_docs:
            return

        texts = [doc["search_text"].strip() for doc in valid_docs]
        
        # 2. Transformation: Call Gemini API for batch embeddings
        embeddings = await embedding_client .embed_batch(texts)

        # 3. Loading: Prepare bulk updates
        updates = []
        for i, embedding in enumerate(embeddings):
            doc_id = valid_docs[i]["_id"]
            updates.append(
                UpdateOne(
                    {"_id": doc_id},
                    {"$set": {"embedding": embedding}}
                )
            )

        if updates:
            await collection.bulk_write(updates)
            logger.info(f"Updated {len(updates)} documents with embeddings")

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise
