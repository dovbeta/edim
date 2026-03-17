from typing import Any, Dict
import logging
import time
from .structured_retriever import StructuredRetriever
from .vector_retriever import VectorRetriever
from planning.plan_models import Plan

logger = logging.getLogger(__name__)

class DataRouter:
    """
    Responsibilities:
    - route to Structured or Vector retrieval based on plan
    """
    def __init__(self, structured_retriever: StructuredRetriever, vector_retriever: VectorRetriever):
        self.structured_retriever = structured_retriever
        self.vector_retriever = vector_retriever
 
    async def retrieve(self, plan: Plan, context: Dict[str, Any] | None = None) -> Any:
        results = {}
        request_id = (context or {}).get("request_id")
        sources = list(getattr(plan, "sources", []) or [])
        logger.info("retrieve.start request_id=%s sources=%s", request_id, sources)

        if "structured_data" in plan.sources:
            t0 = time.perf_counter()
            results["structured_data"] = await self.structured_retriever.retrieve(plan, context=context)
            logger.info(
                "retrieve.structured.done request_id=%s rows=%s ms=%s",
                request_id,
                len(results["structured_data"] or []) if isinstance(results["structured_data"], list) else ("-" if results["structured_data"] is None else 1),
                int((time.perf_counter() - t0) * 1000),
            )
            
        # "vector_knowledge" is the configured source name in Planner.DATA_CATALOG.
        if "vector_knowledge" in plan.sources:
            t1 = time.perf_counter()
            results["vector_knowledge"] = await self.vector_retriever.retrieve(plan, context=context)
            logger.info(
                "retrieve.vector.done request_id=%s chunks=%s ms=%s",
                request_id,
                len(results["vector_knowledge"] or []) if isinstance(results["vector_knowledge"], list) else ("-" if results["vector_knowledge"] is None else 1),
                int((time.perf_counter() - t1) * 1000),
            )

        # Return merged results or primary result
        if len(results) == 1:
            return list(results.values())[0]
        return results if results else None
