from llm.base import LLMClient
from utils.json_safe import to_jsonable

class Responder:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def respond(self, message, context, data, history, plan=None):
        prompt_context = to_jsonable({
            "user_data": context,
            "sql_results": data,
            "plan": plan.__dict__ if plan else None
        })

        print("Generating response")

        return await self.llm.generate(
            message=message,
            context=prompt_context,
            history=history,
        )