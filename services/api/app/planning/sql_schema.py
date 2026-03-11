SQL_SCHEMA = """
Primary query sources:
- units_extended
- unit_residents

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

View units_extended:
- unit_id uuid
- unit_number text
- personal_account text
- unit_type text
- floor int
- section text
- rooms int
- area_total numeric
- debt_total numeric
- building_id uuid
- building_address text
- organization_id uuid
- organization_name text


View unit_residents:
- unit_id uuid
- unit_number text
- unit_type text
- building_id text
- building_address text
- organization_id text
- user_id uuid
- first_name text
- last_name text
- phone text
- resident_role text
"""