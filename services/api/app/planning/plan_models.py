from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Plan:
    intent: str
    sources: List[str]  # ["structured"], ["vector"], []
    query: str
    entities: Optional[List[str]] = None
    filters: Optional[Dict] = None
    structured_query: Optional[str] = None  # Internal for StructuredRetriever
    structured_params: Optional[Dict] = None  # Internal for StructuredRetriever
