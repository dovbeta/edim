from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from policy.edim_policy import Policy


class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        message: str,
        context: Optional[Dict] = None,
        history: Optional[List] = None,
        policy: Optional[Policy] = None
    ) -> str:
        """
        Conversational generation.
        """
        pass

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Raw prompt -> text.
        """
        pass

    @abstractmethod
    async def generate_json(self, prompt: str, retries: int = 2) -> Dict[str, Any]:
        """
        Raw prompt -> JSON.
        """
        pass
