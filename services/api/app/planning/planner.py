from db.models.plan import QueryPlan
from llm.base import LLMClient
from planning.tenant_scope import TenantScope


class Planner:
    def __init__(self, llm, schema, prompt_builder):
        self.llm = llm
        self.schema = schema
        self.prompt_builder = prompt_builder

    async def plan(self, message, context, history):
        prompt = self.prompt_builder.build(
            message=message,
            context=context,
            history=history,
            schema=self.schema,
        )

        result = await self.llm.generate_json(prompt)

        sql = result.get("sql")
        params = result.get("params") or {}

        org_roles = context.get("org_roles", [])
        if sql and org_roles:
            org_id = org_roles[0]["organization_id"]

            scope = TenantScope(org_id)
            sql = scope.apply(sql)

            params["organization_id"] = org_id

        # ✅ tenant injection
        org_roles = context.get("org_roles", [])
        if org_roles:
            org_id = org_roles[0]["organization_id"]

            scope = TenantScope(org_id)
            sql = scope.apply(sql)

            params["organization_id"] = org_id

        return QueryPlan(
            intent=result["intent"],
            needs_sql=result["needs_sql"],
            needs_more_info=result.get("needs_more_info", False),
            sql=sql,
            params=params,
            explanation=result.get("explanation"),
        )