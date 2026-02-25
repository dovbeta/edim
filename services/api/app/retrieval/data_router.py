from typing import Any
from .structured_retriever import StructuredRetriever
from .vector_retriever import VectorRetriever
from planning.plan_models import Plan

class DataRouter:
    """
    Responsibilities:
    - route to Structured or Vector retrieval based on plan
    """
    def __init__(self, structured_retriever: StructuredRetriever, vector_retriever: VectorRetriever):
        self.structured_retriever = structured_retriever
        self.vector_retriever = vector_retriever

    async def retrieve(self, plan: Plan) -> Any:
        results = {}
        
        if "structured" in plan.sources:
            results["structured"] = await self.structured_retriever.retrieve(plan)
            
        if "vector" in plan.sources:
            results["vector"] = await self.vector_retriever.retrieve(plan)
            
        # Return merged results or primary result
        if len(results) == 1:
            return list(results.values())[0]
        return results if results else None
