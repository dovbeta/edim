from typing import List, Dict, Any
from .plan_models import Plan
import logging
import time

logger = logging.getLogger(__name__)


DATA_CATALOG = {
    "resident_address": "structured_data",
    "resident_debt": "structured_data",
    "contacts": "structured_data",
    "vehicles": "structured_data",
    "units": "structured_data",
    "organizations": "structured_data",
    "buildings": "structured_data",
    "roles": "structured_data",

    "rules": "vector_knowledge",
    "faq": "vector_knowledge",
    "services": "vector_knowledge",
    "announcements": "vector_knowledge",

    "greeting": "none",
    "thanks": "none",
    "smalltalk": "none",
    "unknown": "none",
}


class Planner:
    """
    Responsibilities:
    - detect intent
    - decide data source
    - normalize query
    """

    def __init__(self, llm, prompt_builder):
        self.llm = llm
        self.prompt_builder = prompt_builder

    async def plan(
        self,
        message: str,
        history: List[Dict],
        context: Dict[str, Any],
    ) -> Plan:
        request_id = (context or {}).get("request_id")
        t0 = time.perf_counter()
        prompt = self.prompt_builder.build(
            message=message,
            context=context,
            history=history,
        )

        result = await self.llm.generate_json(prompt)

        intent = result.get("intent", "unknown")

        sources: List[str] = []

        source = DATA_CATALOG.get(intent)

        if source:
            sources.append(source)

        # planner explicitly asks for structured data
        if result.get("needs_structured_data"):
            if "structured_data" not in sources:
                sources.append("structured_data")

        # fallback logic
        if not sources:
            sources.append("vector_knowledge")

        # if planner says no data needed
        if intent in ["greeting", "thanks", "smalltalk"]:
            sources = ["none"]

        plan = Plan(
            intent=intent,
            sources=sources,
            query=result.get("query", message),
            entities=result.get("entities"),
            filters=result.get("filters"),
            structured_query=result.get("structured_query"),
            structured_params=result.get("params"),
            needs_more_info=result.get("needs_more_info", False),
            explanation=result.get("explanation"),
        )
        logger.info(
            "planner.done request_id=%s intent=%s sources=%s has_sql=%s ms=%s",
            request_id,
            plan.intent,
            plan.sources,
            bool(plan.structured_query),
            int((time.perf_counter() - t0) * 1000),
        )
        return plan