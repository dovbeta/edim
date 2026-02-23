class SQLValidator:
    def __init__(self, allowed_tables: set):
        self.allowed_tables = allowed_tables

    def validate(self, sql: str, role: str | None = None):
        s = sql.lower()

        if not s.startswith("select"):
            raise ValueError("Only SELECT allowed")

        # Board role has extended permissions: allow bulk selections
        if role == "board":
            return

        forbidden_bulk_patterns = [
            "from users",
            "from vehicles",
            "from user_units",
        ]

        # allow if specific filters exist
        has_specific_filter = any(
            k in s for k in ["license_plate", "personal_account", "first_name", "last_name"]
        )

        if any(p in s for p in forbidden_bulk_patterns) and not has_specific_filter:
            raise ValueError("Bulk neighbor queries are forbidden")