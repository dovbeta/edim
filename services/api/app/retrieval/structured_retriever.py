from typing import Any, Dict
import logging
import time
import re
from planning.plan_models import Plan

logger = logging.getLogger(__name__)

MAX_STRUCTURED_ROWS_FOR_RESPONSE = 10

class TooManyStructuredResultsError(ValueError):
    pass

_CYR_TO_LAT = str.maketrans({
    # upper
    "А": "A",
    "В": "B",
    "Е": "E",
    "І": "I",
    "К": "K",
    "М": "M",
    "Н": "H",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "Х": "X",
    "У": "Y",
    # lower
    "а": "A",
    "в": "B",
    "е": "E",
    "і": "I",
    "к": "K",
    "м": "M",
    "н": "H",
    "о": "O",
    "р": "P",
    "с": "C",
    "т": "T",
    "х": "X",
    "у": "Y",
})


def _normalize_plate_fragment(v: str) -> str:
    # remove spaces/separators, map Cyrillic-lookalikes to Latin, keep alnum only
    s = (v or "").strip().translate(_CYR_TO_LAT)
    s = re.sub(r"[^0-9A-Za-z]+", "", s)
    return s.upper()


def _normalize_plate_param(params: dict | None) -> dict | None:
    if not params:
        return params
    if "license_plate" not in params:
        return params
    frag = _normalize_plate_fragment(str(params.get("license_plate") or ""))
    if not frag:
        return params
    # Always use partial match pattern; DB stores latin plates, often without spaces.
    params = dict(params)
    params["license_plate"] = f"%{frag}%"
    return params


class StructuredRetriever:
    """
    Responsibilities:
    - build query from plan
    - access existing structured data layer (DB/API)
    - return structured records
    """
    def __init__(self, executor, validator):
        self.executor = executor
        self.validator = validator

    async def retrieve(self, plan: Plan, context: Dict[str, Any] = None) -> Any:
        if not plan.structured_query:
            return None

        # Normalize common user input patterns (e.g., car plates).
        plan.structured_params = _normalize_plate_param(plan.structured_params)
        
        # Validation
        request_id = (context or {}).get("request_id")
        role = None
        if context:
            # очікується, що роль користувача/організації буде в контексті
            role = context.get("role") or context.get("user_role")
        logger.info(
            "structured.validate request_id=%s role=%s has_params=%s",
            request_id,
            role,
            bool(plan.structured_params),
        )
        self.validator.validate(plan.structured_query, role=role)
        
        # Execution
        t0 = time.perf_counter()
        data = await self.executor.run(
            plan.structured_query,
            plan.structured_params,
            context=context
        )
        if isinstance(data, list) and len(data) > MAX_STRUCTURED_ROWS_FOR_RESPONSE:
            raise TooManyStructuredResultsError(
                f"Too many structured results: {len(data)} (max {MAX_STRUCTURED_ROWS_FOR_RESPONSE})"
            )
        logger.info(
            "structured.execute.ok request_id=%s rows=%s ms=%s",
            request_id,
            len(data or []),
            int((time.perf_counter() - t0) * 1000),
        )
        return data
