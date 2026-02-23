from policy.edim_policy import EDIMAccessPolicy


class PlannerPromptBuilder:
    """
    Builds the planning prompt for LLM.
    LLM must decide:
    - intent
    - needs_sql
    - sql
    - params
    """

    def __init__(self, schema: str):
        self.schema = schema

    def build(
        self,
        message: str,
        context: dict,
        history: list,
        schema: str | None = None,
    ) -> str:
        schema_text = schema or self.schema

        role = EDIMAccessPolicy.resolve_role(context)
        policy = EDIMAccessPolicy.get_policy(role)

        user = context.get("user", {})
        properties = context.get("properties", [])

        user_id = user.get("id")

        user_info = f"""
User:
- id: {user_id}
- name: {user.get("name")}
"""

        # buildings user belongs to
        buildings = set()
        for p in properties:
            b = p.get("building", {}).get("id")
            if b:
                buildings.add(b)

        buildings_text = ""
        if buildings:
            buildings_text = "User buildings:\n" + "\n".join(
                f"- {b}" for b in buildings
            )

        properties_text = ""
        if properties:
            props_lines = []
            for p in properties:
                props_lines.append(
                    f"- unit {p.get('unit_number')} ({p.get('unit_type')}), building: {p.get('building', {}).get('address')}"
                )
            properties_text = "User properties:\n" + "\n".join(props_lines)

        history_text = ""
        if history:
            msgs = []
            for h in history[-4:]:
                role = h.get("role")
                text = h.get("text")
                msgs.append(f"{role}: {text}")
            history_text = "Recent conversation:\n" + "\n".join(msgs)

        prompt = f"""
You are EDIM Copilot SQL planner.

Your task:
Understand the user question and decide if database data is required.

User role: {policy.role_name}

{policy.to_str()}

SQL RULES:
- ONLY SELECT queries
- NO INSERT/UPDATE/DELETE
- Use ONLY provided schema
- ALWAYS use parameterized SQL (:param)
- NEVER hardcode user_id or building_id
- Aggregations MUST be aliased as value
- If filtering by multiple values use: column = ANY(:param)
- Car plate searches MUST use partial match with ILIKE and wildcards
- If searching by an identifier (license_plate, phone, unit_number, document, etc),
  the SELECT MUST include that full identifier column from the database.
  
ORGANIZATION FILTER RULE:

If organization_id is available in context (org_roles or properties),
ALWAYS filter directly by:
buildings.organization_id = :organization_id

DO NOT determine current user's organization via SQL joins or subqueries.

DO NOT use aliases like current_user (reserved in PostgreSQL).

Membership and access scope are already enforced by the system context.

If data is required:
Return SQL and params.

If you cannot fulfill the request because you need more information from the user (e.g. which unit, which person, or missing car plate), set needs_more_info to true and explain what is missing.

Return JSON:
- intent: snake_case
- needs_sql: true/false
- needs_more_info: true/false
- sql: SQL or null
- params: dict or null
- explanation: short explanation for the system or what information is missing from the user

IDENTIFIER RESPONSE RULE:
When user searches by partial identifier:
- SQL MUST use partial match (ILIKE)
- SQL MUST SELECT the full identifier column
- Response MUST display the full identifier from DB
- NEVER echo only the user fragment

IMPORTANT:
To determine user's organization, use property chain:
users → user_units → units → buildings → organizations.

DO NOT use user_organizations to determine membership.
user_organizations only stores roles like board/manager.

Database schema:
{schema_text}

{user_info}

{buildings_text}

{properties_text}

{history_text}

User message:
\"\"\"{message}\"\"\"

Return ONLY valid JSON.
"""
        return prompt.strip()