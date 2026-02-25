import traceback
from typing import Any, Dict, Optional

class FailureLoggerService:
    def __init__(self, repo):
        self.repo = repo

    async def log_failure(
        self,
        component: str,
        exception: Exception,
        meta: Optional[Dict[str, Any]] = None,
    ):
        error_message = str(exception)
        error_type = type(exception).__name__
        stack_trace = traceback.format_exc()

        await self.repo.add_failure(
            component=component,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            meta=meta,
        )
