import re


class PolicyError(Exception):
    """Raised when a security or tenant-scope policy is violated."""


class ScopeEnforcer:

    def apply(self, plan, context):

        if not plan.structured_query:
            return plan

        sql = plan.structured_query
        params = plan.structured_params or {}

        scope = context.get("scope", {})
        building_ids = scope.get("building_ids", [])

        if not building_ids:
            raise PolicyError("No building scope available for structured query")

        lower = sql.lower()

        # ------------------------------------------------------------------
        # Special case: management/board lookups (users + user_organizations)
        # ------------------------------------------------------------------
        is_management_lookup = (
            re.search(r"\bfrom\s+users\b", lower)
            and re.search(r"\bjoin\s+user_organizations\b", lower)
        )
        if is_management_lookup:
            # 1) Приберемо можливий сирий фільтр по building_id, який міг
            # згенерувати планер (в users/user_organizations цієї колонки немає).
            sql = re.sub(
                r"\bwhere\s+building_id\s*=\s*any\([^)]*\)\s*and\s+",
                "WHERE ",
                sql,
                flags=re.IGNORECASE,
            )
            lower = sql.lower()

            # 2) Додамо скоуп по organization_id через units_extended.
            clause = (
                "uo.organization_id IN ("
                "SELECT DISTINCT organization_id FROM units_extended "
                "WHERE building_id = ANY(:building_ids)"
                ")"
            )

            if " where " in lower:
                sql = re.sub(r"\bwhere\b", f"WHERE {clause} AND", sql, flags=re.IGNORECASE)
            else:
                match = re.search(r"\b(group by|order by|limit)\b", lower)
                if match:
                    idx = match.start()
                    sql = sql[:idx] + f" WHERE {clause} " + sql[idx:]
                else:
                    sql += f" WHERE {clause}"

            params["building_ids"] = building_ids
            plan.structured_query = sql
            plan.structured_params = params
            return plan

        # ------------------------------------------------------------------
        # Default: inject building scope only when safe
        # ------------------------------------------------------------------
        if "building_id" in lower:
            clause = "building_id = ANY(:building_ids)"
        elif re.search(r"\bfrom\s+buildings\b", lower) or re.search(r"\bjoin\s+buildings\b", lower):
            clause = "buildings.id = ANY(:building_ids)"
        else:
            # Can't safely scope by building; leave SQL as-is.
            plan.structured_query = sql
            plan.structured_params = params
            return plan

        if " where " in lower:
            sql = re.sub(r"\bwhere\b", f"WHERE {clause} AND", sql, flags=re.IGNORECASE)
        else:
            match = re.search(r"\b(group by|order by|limit)\b", lower)
            if match:
                idx = match.start()
                sql = sql[:idx] + f" WHERE {clause} " + sql[idx:]
            else:
                sql += f" WHERE {clause}"

        params["building_ids"] = building_ids

        plan.structured_query = sql
        plan.structured_params = params

        return plan