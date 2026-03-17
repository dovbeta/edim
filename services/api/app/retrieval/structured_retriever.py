from typing import Any, Dict
from planning.plan_models import Plan

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
        role = None
        if context:
            # очікується, що роль користувача/організації буде в контексті
            role = context.get("role") or context.get("user_role")
        self.validator.validate(plan.structured_query, role=role)
        
        # Execution
        data = await self.executor.run(
            plan.structured_query,
            plan.structured_params,
            context=context
        )
        print(f"Retrieved {len(data)} records from structured data source")
        return data
