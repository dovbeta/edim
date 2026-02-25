from llm.base import LLMClient
from utils.json_safe import to_jsonable

class Responder:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def respond(self, message, context, data, history, plan=None, error=None):
        # Compatibility with new Plan object
        plan_dict = None
        if plan:
            plan_dict = plan.__dict__.copy()
            # For backward compatibility in prompt if needed
            plan_dict["sql"] = plan.structured_query
            plan_dict["params"] = plan.structured_params
            plan_dict["needs_sql"] = "structured" in plan.sources

        prompt_context = to_jsonable({
            "user_data": context,
            "sql_results": data,
            "plan": plan_dict,
            "error": error
        })

        print("Generating response")

        return await self.llm.generate(
            message=message,
            context=prompt_context,
            history=history,
        )