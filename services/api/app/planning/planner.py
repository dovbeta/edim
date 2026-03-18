from typing import List, Dict, Any
from .plan_models import Plan
import logging
import time
import re

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
    "neighbors_on_floor": "structured_data",
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
        # Deterministic intent: neighbors on the same floor
        msg_l = (message or "").lower()
        if re.search(r"сусід(и|ів)?\s+на\s+поверс|мої\s+сусід|сусіди\s+на\s+моєму\s+поверс", msg_l):
            props = context.get("properties", []) or []
            # choose apartment-like properties only
            apartment_props = [
                p for p in props
                if str(p.get("unit_type") or "").lower() in {"apartment", "квартира"}
            ]
            if len(apartment_props) != 1:
                explanation = None
                if not apartment_props:
                    explanation = "Я не бачу у вашому профілі квартири. Уточніть, будь ласка, номер квартири та адресу будинку."
                else:
                    opts = []
                    for p in apartment_props[:5]:
                        addr = (p.get("building") or {}).get("address")
                        opts.append(f"- квартира {p.get('unit_number')} (будинок: {addr})")
                    explanation = (
                        "У вас є кілька квартир. Уточніть, для якої квартири шукати сусідів на поверсі:\n"
                        + "\n".join(opts)
                    )
                plan = Plan(
                    intent="neighbors_on_floor",
                    sources=["structured_data"],
                    query=message,
                    needs_more_info=True,
                    explanation=explanation,
                )
                logger.info(
                    "planner.done request_id=%s intent=%s sources=%s has_sql=%s ms=%s",
                    request_id,
                    plan.intent,
                    plan.sources,
                    False,
                    int((time.perf_counter() - t0) * 1000),
                )
                return plan

            p = apartment_props[0]
            building = p.get("building") or {}
            building_id = building.get("id")
            section = p.get("section")
            floor = p.get("floor")
            unit_id = p.get("unit_id")

            if not building_id or section is None or floor is None or not unit_id:
                plan = Plan(
                    intent="neighbors_on_floor",
                    sources=["structured_data"],
                    query=message,
                    needs_more_info=True,
                    explanation="Уточніть, будь ласка, будинок/підʼїзд/поверх для вашої квартири — я не бачу повних даних у профілі.",
                )
                logger.info(
                    "planner.done request_id=%s intent=%s sources=%s has_sql=%s ms=%s",
                    request_id,
                    plan.intent,
                    plan.sources,
                    False,
                    int((time.perf_counter() - t0) * 1000),
                )
                return plan

            plan = Plan(
                intent="neighbors_on_floor",
                sources=["structured_data"],
                query=message,
                structured_query=(
                    "SELECT first_name, last_name, unit_number, unit_type, floor, section, building_address "
                    "FROM unit_residents "
                    "WHERE building_id = :building_id "
                    "AND section = :section "
                    "AND floor = :floor "
                    "AND lower(trim(unit_type)) = ANY(:unit_types) "
                    "AND unit_id != :unit_id "
                    "ORDER BY unit_number, last_name"
                ),
                structured_params={
                    "building_id": building_id,
                    "section": str(section),
                    "floor": int(floor) if isinstance(floor, int) else str(floor),
                    "unit_types": ["apartment", "квартира"],
                    "unit_id": unit_id,
                },
            )
            logger.info(
                "planner.done request_id=%s intent=%s sources=%s has_sql=%s ms=%s",
                request_id,
                plan.intent,
                plan.sources,
                True,
                int((time.perf_counter() - t0) * 1000),
            )
            return plan

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