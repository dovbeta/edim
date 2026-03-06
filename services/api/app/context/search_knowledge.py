from motor.motor_asyncio import AsyncIOMotorClient
from llm.openai_embed import OpenAIEmbeddingClient
import os


async def search_knowledge(query: str, organization_id: str):

    mongo = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = mongo["edim"]
    collection = db["knowledge"]

    embed_client = OpenAIEmbeddingClient()

    # embedding запиту
    query_embedding = await embed_client.embed(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "knowledge_vector",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 5,
                "filter": {
                    "organization_id": organization_id
                }
            }
        },
        {
            "$project": {
                "search_text": 1,
                "type": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = []
    async for doc in collection.aggregate(pipeline):
        results.append(doc)

    return results