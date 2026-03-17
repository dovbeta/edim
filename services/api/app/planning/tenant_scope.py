class TenantScope:
    def __init__(self, org_id: str):
        self.org_id = org_id

    def apply(self, sql: str | None) -> str | None:
        if not sql:
            return sql

        if "organization_id" in sql.lower():
            return sql

        # if " join buildings " in sql.lower():
        #     return sql.replace(
        #         "WHERE",
        #         "WHERE buildings.organization_id = :organization_id AND "
        #     )

        return sql