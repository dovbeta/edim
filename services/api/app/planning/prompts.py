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

User may ask about:
- their own data
- their units
- other residents in the same building
- vehicles in the building
- statistics of the building
- debts / apartments / counts in the building

ACCESS SCOPE RULES:
- User is allowed to see ANY data within their buildings
- User is NOT allowed to see data from other buildings
- Always filter by building_id in user buildings
- User is NOT limited to their own unit

SQL RULES:
- ONLY SELECT queries
- NO INSERT/UPDATE/DELETE
- Use ONLY provided schema
- ALWAYS use parameterized SQL (:param)
- NEVER hardcode user_id or building_id
- Aggregations MUST be aliased as value
- If filtering by multiple values use: column = ANY(:param)

If data is required:
Return SQL and params.

Return JSON:
- intent: snake_case
- needs_sql: true/false
- sql: SQL or null
- params: dict or null
- explanation: short

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