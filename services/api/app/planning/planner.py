from db.models.plan import QueryPlan


class Planner:
    def __init__(self, llm, schema, prompt_builder):
        self.llm = llm
        self.schema = schema
        self.prompt_builder = prompt_builder

    async def plan(self, message, context, history) -> QueryPlan:
        print("Planning query for message:", message)
        prompt = self.prompt_builder.build(
            message=message,
            context=context,
            history=history,
            schema=self.schema,
        )

        result = await self.llm.generate_json(prompt)
        print("Result:", result)

        return QueryPlan(
            intent=result["intent"],
            needs_sql=result["needs_sql"],
            sql=result.get("sql"),
            params=result.get("params"),
            explanation=result.get("explanation"),
        )