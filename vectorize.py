import os
import logging
import argparse
from typing import List, Dict, Any

from pymongo import MongoClient, UpdateOne
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MONGODB_URI = os.getenv("MONGODB_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_NAME = "osbb"
COLLECTION_NAME = "knowledge"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50

def get_mongo_client() -> MongoClient:
    """Connect to MongoDB Atlas."""
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable is not set")
    return MongoClient(MONGODB_URI)

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=OPENAI_API_KEY)

def vectorize_documents(organization_id: str):
    """
    ETL process to vectorize documents:
    1. Extract: Find documents for the given organization_id without an 'embedding' field.
    2. Transform: Generate embeddings for 'search_text' using OpenAI API.
    3. Load: Save embeddings back to MongoDB in batches.
    """
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        openai_client = get_openai_client()

        # 1. Extraction: Query for documents missing the 'embedding' field for the specific organization
        query = {
            "organization_id": organization_id,
            "embedding": {"$exists": False}
        }
        total_docs = collection.count_documents(query)
        
        if total_docs == 0:
            logger.info(f"No documents found for organization '{organization_id}' that require vectorization.")
            return

        logger.info(f"Found {total_docs} documents for organization '{organization_id}' to process.")

        # Initialize progress bar
        with tqdm(total=total_docs, desc=f"Vectorizing {organization_id}") as pbar:
            cursor = collection.find(query)
            batch: List[Dict[str, Any]] = []

            for doc in cursor:
                batch.append(doc)

                # Process in batches of BATCH_SIZE
                if len(batch) >= BATCH_SIZE:
                    process_batch(collection, openai_client, batch)
                    pbar.update(len(batch))
                    batch = []

            # Process remaining documents in the final batch
            if batch:
                process_batch(collection, openai_client, batch)
                pbar.update(len(batch))

        logger.info("Vectorization completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the vectorization process: {e}")
    finally:
        if 'mongo_client' in locals():
            mongo_client.close()

def process_batch(collection, openai_client: OpenAI, batch: List[Dict[str, Any]]):
    """
    Process a single batch of documents:
    - Extract search_text from each document.
    - Call OpenAI API to get embeddings for the entire batch.
    - Prepare bulk updates for MongoDB.
    """
    try:
        # Prepare texts for embedding
        # Filter out documents with empty search_text to avoid API errors
        texts = [doc.get("search_text", "").strip() for doc in batch]
        valid_indices = [i for i, text in enumerate(texts) if text]
        
        if not valid_indices:
            return

        valid_texts = [texts[i] for i in valid_indices]

        # 2. Transformation: Call OpenAI API (batching embeddings is more efficient)
        response = openai_client.embeddings.create(
            input=valid_texts,
            model=EMBEDDING_MODEL
        )

        # 3. Loading: Prepare bulk updates
        updates = []
        for i, embedding_data in enumerate(response.data):
            doc_index = valid_indices[i]
            doc_id = batch[doc_index]["_id"]
            updates.append(
                UpdateOne(
                    {"_id": doc_id},
                    {"$set": {"embedding": embedding_data.embedding}}
                )
            )

        if updates:
            collection.bulk_write(updates)

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        # In production, you might want to retry or log specific failed IDs
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vectorize knowledge documents for a specific organization.")
    parser.add_argument("organization_id", help="The ID of the organization whose documents should be vectorized.")
    args = parser.parse_args()

    vectorize_documents(args.organization_id)
