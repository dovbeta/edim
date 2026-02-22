class SQLValidator:
    def __init__(self, allowed_tables: set):
        self.allowed_tables = allowed_tables

    def validate(self, sql: str):
        s = sql.lower().strip()

        if not s.startswith("select"):
            raise ValueError("Only SELECT allowed")

        for forbidden in ["insert", "update", "delete", "drop"]:
            if forbidden in s:
                raise ValueError("Mutation not allowed")

        # тут можна підключити sqlglot/pglast