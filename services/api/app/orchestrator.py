from context_manager import ContextManager
from llm_client import GeminiClient


class Orchestrator:
    def __init__(self):
        self.context = ContextManager()
        self.llm = GeminiClient()

    async def handle(self, message, user_id):

        answer = await self.llm.generate(message)
        return answer