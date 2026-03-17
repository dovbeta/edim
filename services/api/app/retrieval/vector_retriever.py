from typing import Any, List, Dict
import logging
import time

from planning.plan_models import Plan

logger = logging.getLogger(__name__)


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

    async def retrieve(self, plan: Plan, context: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        request_id = (context or {}).get("request_id")
        scope = (context or {}).get("scope", {}) or {}
        org_ids = scope.get("organization_ids") or []
        org_id = org_ids[0] if org_ids else None

        t0 = time.perf_counter()
        logger.info("vector.start request_id=%s org_id=%s query_len=%s", request_id, org_id, len(plan.query or ""))

        # 1️⃣ create embedding
        query_embedding = await self.embedding_client.embed(plan.query)

        # 2️⃣ vector search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": 5,
                    "filter": ({"organization_id": org_id} if org_id else {})
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
        logger.info(
            "vector.done request_id=%s chunks=%s ms=%s",
            request_id,
            len(results),
            int((time.perf_counter() - t0) * 1000),
        )

        return results