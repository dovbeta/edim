from sqlalchemy import text


class SQLExecutor:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def run(self, sql: str, params: dict | None = None):
        async with self.session_factory() as session:
            result = await session.execute(
                text(sql),
                params or {},
            )

            rows = result.mappings().all()

            # convert to plain dicts
            return [dict(r) for r in rows]