SQL_SCHEMA = """
Table users:
- id uuid
- first_name text
- last_name text
- phone text

Table organizations:
- id uuid
- name text

Table buildings:
- id uuid
- address text
- organization_id uuid

Table units:
- id uuid
- number text
- personal_account text
- unit_type text
- floor int
- section text
- rooms int
- area_total numeric
- debt_total numeric
- building_id uuid

Table user_units:
- user_id uuid
- unit_id uuid
- role text

Table user_organizations:
- id uuid
- user_id uuid
- organization_id uuid
- role text

Table vehicles:
- id uuid
- user_id uuid
- model text
- license_plate text

"""