import re

class ScopeEnforcer:

    def apply(self, plan, context):

        if not plan.structured_query:
            return plan

        sql = plan.structured_query
        params = plan.structured_params or {}

        scope = context.get("scope", {})
        building_ids = scope.get("building_ids", [])

        if not building_ids:
            return plan

        clause = "building_id = ANY(:building_ids)"

        lower = sql.lower()

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