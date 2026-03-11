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

    def __init__(self, schema: str, data_catalog: dict):
        self.schema = schema
        self.data_catalog = data_catalog

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
                debt_info = f", debt: {p.get('debt_total')}" if p.get('debt_total') is not None else ""
                props_lines.append(
                    f"- unit {p.get('unit_number')} ({p.get('unit_type')}), building: {p.get('building', {}).get('address')}{debt_info}"
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

        # ----- DATA CATALOG -----

        catalog_lines = []

        for intent, source in self.data_catalog.items():
            catalog_lines.append(f"- {intent}: {source}")

        catalog_text = "\n".join(catalog_lines)

        prompt = f"""
You are EDIM Copilot SQL planner.

Your task:
Understand the user question and decide if database data is required.

AVAILABLE INTENTS AND THEIR DATA SOURCES:

{catalog_text}
Instructions:
1. First try to select the MOST APPROPRIATE intent from the list above.
2. If none of the intents match the user message well, you MAY create a NEW intent name.
3. If you create a new intent, choose the most appropriate data source:
   - structured_data
   - vector_knowledge
   - none

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
  
Join conditions MUST use real primary/foreign key columns exactly as defined in the schema.

Do NOT invent column names.
  
TENANT SCOPING RULE:

Organization and tenant filtering are automatically applied by the system.
DO NOT include organization_id in SQL.
DO NOT include organization_id in params.
DO NOT filter by organization manually.

UNIT TYPE RULE
The field unit_type describes the type of premises.
If the user explicitly mentions the type of premises,
the SQL query MUST include a filter on unit_type.

Always write queries as if data is already limited to the user's organization.

DO NOT determine current user's organization via SQL joins or subqueries.

DO NOT use aliases like current_user (reserved in PostgreSQL).

Membership and access scope are already enforced by the system context.

If data is required from structured sources:

Return:
- needs_structured_data: true
- structured_query
- params

If structured data is NOT required:
needs_structured_data: false
structured_query: null
params: null

IDENTIFIER RESPONSE RULE:
When user searches by partial identifier:
- SQL MUST use partial match (ILIKE)
- SQL MUST SELECT the full identifier column
- Response MUST display the full identifier from DB
- NEVER echo only the user fragment

================ USER LANGUAGE NORMALIZATION ================

Users may refer to apartments using shorthand notation.

Interpret the following patterns as unit (apartment) numbers:

- "к60" → unit_number = 60
- "кв60" → unit_number = 60
- "кв.60" → unit_number = 60
- "кв 60" → unit_number = 60
- "к 60" → unit_number = 60

If a building number or unit number contains a letter
(for example: 12а, 7Б, 15В):

- The letter MUST be interpreted as a Ukrainian Cyrillic letter.
- NEVER treat such letters as Latin characters.

The letters "к" or "кв" mean apartment/unit.

When such shorthand is used:
- treat it as unit_number filter
- SQL MUST filter by u.number = :unit_number

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