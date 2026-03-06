from typing import List, Dict, Any
from .plan_models import Plan


DATA_CATALOG = {
    "resident_address": "structured",
    "resident_debt": "structured",
    "contacts": "structured",
    "vehicles": "structured",
    "units": "structured",

    "rules": "vector",
    "faq": "vector",
    "services": "vector",
    "announcements": "vector",
}


class Planner:
    """
    Responsibilities:
    - detect intent from user message + history
    - decide data source (structured / vector)
    - return Plan object
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

        prompt = self.prompt_builder.build(
            message=message,
            context=context,
            history=history,
        )

        result = await self.llm.generate_json(prompt)

        intent = result.get("intent", "unknown")

        sources: List[str] = []

        # mapping intent → source
        source = DATA_CATALOG.get(intent)

        if source:
            sources.append(source)

        # якщо LLM вирішив що потрібен SQL
        if result.get("needs_sql"):
            if "structured" not in sources:
                sources.append("structured")


        # якщо intent невідомий — fallback на vector
        if not sources:
            sources.append("vector")

        return Plan(
            intent=intent,
            sources=sources,
            query=result.get("query", message),
            entities=result.get("entities"),
            filters=result.get("filters"),
            structured_query=result.get("sql"),
            structured_params=result.get("params"),
        )