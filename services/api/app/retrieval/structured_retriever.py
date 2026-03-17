from typing import Any, Dict
import logging
import time
from planning.plan_models import Plan

logger = logging.getLogger(__name__)

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
        logger.info(
            "structured.execute.ok request_id=%s rows=%s ms=%s",
            request_id,
            len(data or []),
            int((time.perf_counter() - t0) * 1000),
        )
        return data
