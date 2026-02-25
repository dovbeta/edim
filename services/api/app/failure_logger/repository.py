from datetime import datetime
from typing import Any, Dict, Optional

class FailureLoggerRepository:
    def __init__(self, collection):
        self.col = collection

    async def add_failure(
        self,
        component: str,
        error_message: str,
        error_type: str,
        stack_trace: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        doc = {
            "component": component,
            "error_message": error_message,
            "error_type": error_type,
            "stack_trace": stack_trace,
            "meta": meta or {},
            "created_at": datetime.utcnow(),
        }
        await self.col.insert_one(doc)
