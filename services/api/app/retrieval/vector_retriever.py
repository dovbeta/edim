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

        t0 = time.perf_counter()
        logger.info(
            "vector.start request_id=%s org_ids=%s query_len=%s query_preview=%s",
            request_id,
            org_ids,
            len(plan.query or ""),
            (plan.query or "")[:200].replace("\n", " "),
        )

        # 1️⃣ create embedding
        query_embedding = await self.embedding_client.embed(plan.query)

        # 2️⃣ vector search pipeline
        # Build organization filter: single id -> equality, many -> $in, none -> no filter
        if len(org_ids) == 1:
            filter_doc = {"organization_id": org_ids[0]}
        elif len(org_ids) > 1:
            filter_doc = {"organization_id": {"$in": org_ids}}
        else:
            filter_doc = {}

        logger.info(
            "vector.filter request_id=%s filter=%s",
            request_id,
            filter_doc,
        )

        def build_pipeline(filter_):
            return [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": 5,
                    "filter": filter_
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

        pipeline = build_pipeline(filter_doc)

        async for doc in self.collection.aggregate(pipeline):
            results.append(doc)

        if results:
            preview = [
                {
                    "type": d.get("type"),
                    "score": d.get("score"),
                    "search_text": (d.get("search_text") or "")[:120].replace("\n", " "),
                }
                for d in results[:3]
            ]
            logger.info(
                "vector.results.sample request_id=%s sample=%s",
                request_id,
                preview,
            )

        # If фільтр по organization_id нічого не дав, пробуємо без фільтра
        if not results and filter_doc:
            logger.info(
                "vector.retry_without_filter request_id=%s org_ids=%s",
                request_id,
                org_ids,
            )
            async for doc in self.collection.aggregate(build_pipeline({})):
                results.append(doc)
            if results:
                preview = [
                    {
                        "type": d.get("type"),
                        "score": d.get("score"),
                        "search_text": (d.get("search_text") or "")[:120].replace("\n", " "),
                    }
                    for d in results[:3]
                ]
                logger.info(
                    "vector.results.sample_no_filter request_id=%s sample=%s",
                    request_id,
                    preview,
                )
        logger.info(
            "vector.done request_id=%s chunks=%s ms=%s",
            request_id,
            len(results),
            int((time.perf_counter() - t0) * 1000),
        )

        return results