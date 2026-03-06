from typing import Any, List, Dict

from openai import organization

from planning.plan_models import Plan


class VectorRetriever:
    """
    Responsibilities:
    - create embedding from plan.query
    - search Mongo Atlas vector store
    - return top semantic matches
    """

    def __init__(self, collection, embedding_client):
        self.collection = collection
        self.embedding_client = embedding_client

    async def retrieve(self, plan: Plan) -> List[Dict[str, Any]]:
        print(plan)

        # 1️⃣ create embedding
        query_embedding = await self.embedding_client.embed(plan.query)
        #print(f"Query embedding created: {query_embedding}")

        # 2️⃣ vector search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": 5,
                    "filter": {
                        #"organization_id": organization_id
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "type": 1,
                    "search_text": 1,
                    "payload": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        # 3️⃣ execute query
        results = []

        async for doc in self.collection.aggregate(pipeline):
            results.append(doc)

        print("Vector results:", results)

        return results