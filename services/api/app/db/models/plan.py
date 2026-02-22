from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryPlan:
    intent: str
    needs_sql: bool
    sql: Optional[str] = None
    params: Optional[dict] = None
    explanation: Optional[str] = None