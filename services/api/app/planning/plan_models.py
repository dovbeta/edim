from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Plan:
    intent: str

    # structured_data | vector_knowledge | none
    sources: List[str]

    # normalized query used by retrievers
    query: str

    # extracted entities
    entities: Optional[List[str]] = None

    # additional filters
    filters: Optional[Dict] = None

    # internal query for structured data retriever
    structured_query: Optional[str] = None

    # parameters for structured retriever
    structured_params: Optional[Dict] = None

    # planner may request clarification
    needs_more_info: bool = False

    # explanation for system / logs
    explanation: Optional[str] = None