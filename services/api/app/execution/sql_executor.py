from sqlalchemy import text


def inject_scope_params(sql: str, params: dict | None, context: dict) -> dict:
    params = dict(params or {})

    if "organization_id" in sql and not params.get("organization_id"):
        org_roles = context.get("org_roles", [])
        if org_roles:
            params["organization_id"] = org_roles[0]["organization_id"]

    return params


class SQLExecutor:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def run(
        self,
        sql: str,
        params: dict | None = None,
        context: dict | None = None,
    ):
        scoped_params = inject_scope_params(sql, params, context or {})

        async with self.session_factory() as session:
            result = await session.execute(
                text(sql),
                scoped_params,
            )

            rows = result.mappings().all()
            return [dict(r) for r in rows]