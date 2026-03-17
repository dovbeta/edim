class SQLValidator:
    def __init__(self, allowed_tables: set):
        self.allowed_tables = allowed_tables

    def validate(self, sql: str, role: str | None = None):
        s = sql.lower().strip()

        if not s.startswith("select"):
            raise ValueError("Only SELECT allowed")

        for table in self.allowed_tables:
            if f" {table} " in s or f"{table}." in s:
                break
        else:
            # No allowed table referenced at all
            raise ValueError("Query references disallowed tables")

        # Organization leaders have extended permissions: allow bulk selections
        if role in {"board", "board_member", "manager"}:
            return

        forbidden_bulk_patterns = [
            "from users",
            "from vehicles",
            "from user_units",
        ]

        # allow if specific filters exist
        has_specific_filter = any(
            k in s for k in ["license_plate", "personal_account", "first_name", "last_name", "debt_total"]
        )

        if any(p in s for p in forbidden_bulk_patterns) and not has_specific_filter:
            raise ValueError("Bulk neighbor queries are forbidden")