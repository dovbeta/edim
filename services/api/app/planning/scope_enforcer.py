import re


class PolicyError(Exception):
    """Raised when a security or tenant-scope policy is violated."""


_LAT_TO_CYR_LOOKALIKE = str.maketrans({
    # upper
    "A": "А",
    "B": "В",
    "C": "С",
    "E": "Е",
    "H": "Н",
    "I": "І",
    "K": "К",
    "M": "М",
    "O": "О",
    "P": "Р",
    "T": "Т",
    "X": "Х",
    "Y": "У",
    # lower
    "a": "а",
    "b": "в",
    "c": "с",
    "e": "е",
    "h": "н",
    "i": "і",
    "k": "к",
    "m": "м",
    "o": "о",
    "p": "р",
    "t": "т",
    "x": "х",
    "y": "у",
})


def _normalize_unit_number(value: object) -> str:
    """
    Normalizes unit/building numbers like:
    - "110а", "110 а", "110А", "110A" -> "110а"
    Keeps digits + Ukrainian Cyrillic suffix letters (maps Latin lookalikes to Cyrillic).
    """
    s = str(value or "").strip()
    s = re.sub(r"\s+", "", s)
    s = s.translate(_LAT_TO_CYR_LOOKALIKE)
    m = re.match(r"^(\d+)([^\d]+)?$", s)
    if not m:
        return s
    num = m.group(1)
    suf = (m.group(2) or "").strip()
    return num + suf.lower()


class ScopeEnforcer:

    def apply(self, plan, context):

        if not plan.structured_query:
            return plan

        sql = plan.structured_query
        params = plan.structured_params or {}

        # Normalize common numeric identifiers (unit/building numbers with Cyrillic suffixes).
        if isinstance(params, dict):
            if "unit_number" in params and params.get("unit_number") is not None:
                params = dict(params)
                params["unit_number"] = _normalize_unit_number(params["unit_number"])
            if "building_number" in params and params.get("building_number") is not None:
                params = dict(params)
                params["building_number"] = _normalize_unit_number(params["building_number"])

        scope = context.get("scope", {})
        building_ids = scope.get("building_ids", [])

        if not building_ids:
            raise PolicyError("No building scope available for structured query")

        lower = sql.lower()

        # ------------------------------------------------------------------
        # Normalize unit_type filters (case/whitespace tolerant)
        # If planner generated `unit_type = :unit_type` we rewrite it to:
        #   lower(trim(unit_type)) = ANY(:unit_types)
        # and populate unit_types from the provided param.
        # ------------------------------------------------------------------
        if "unit_type" in lower and re.search(r":unit_type\b", lower):
            raw = (params or {}).get("unit_type")
            unit_types = None
            if raw is not None:
                v = str(raw).strip().lower()
                # expand to common synonyms in DB
                if v in {"apartment", "квартира"} or "кварт" in v:
                    unit_types = ["apartment", "квартира"]
                elif v in {"parking", "паркомісце", "паркінг"} or "паркін" in v or "парком" in v:
                    unit_types = ["parking", "паркомісце", "паркінг"]
                elif v in {"storage", "комора", "кладова"} or "комор" in v or "кладов" in v:
                    unit_types = ["storage", "комора", "кладова"]
                else:
                    unit_types = [v]

            # Replace both qualified and unqualified comparisons so we don't end up with `ur.lower(...)`
            # Example: `ur.unit_type = :unit_type` -> `lower(trim(ur.unit_type)) = ANY(:unit_types)`
            sql = re.sub(
                r"(?i)\b([a-zA-Z_]\w*)\.unit_type\s*=\s*:unit_type\b",
                r"lower(trim(\1.unit_type)) = ANY(:unit_types)",
                sql,
            )
            sql = re.sub(
                r"(?i)\bunit_type\s*=\s*:unit_type\b",
                r"lower(trim(unit_type)) = ANY(:unit_types)",
                sql,
            )

            params = dict(params or {})
            # Drop old unit_type, replace with normalized list
            params.pop("unit_type", None)
            if unit_types:
                params["unit_types"] = [t.strip().lower() for t in unit_types]

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
        # Default: inject building scope
        # ------------------------------------------------------------------
        # If query reads from a relation that contains building_id, we can always
        # inject building scope even when the SQL doesn't already reference it.
        from_has_building_id = bool(
            re.search(r"\bfrom\s+(unit_residents|units_extended|units)\b", lower)
        )

        if from_has_building_id:
            clause = "building_id = ANY(:building_ids)"
        elif re.search(r"\bfrom\s+buildings\b", lower) or re.search(r"\bjoin\s+buildings\b", lower):
            clause = "buildings.id = ANY(:building_ids)"
        elif "building_id" in lower:
            clause = "building_id = ANY(:building_ids)"
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

        # ------------------------------------------------------------------
        # Unit type safety: якщо користувач явно питає "квартира/паркомісце/комора",
        # а SQL не має фільтру unit_type, додаємо його (щоб не змішувати юніти з
        # однаковими номерами різних типів).
        # ------------------------------------------------------------------
        q = (getattr(plan, "query", None) or "").lower()
        desired_unit_types = None
        if re.search(r"\bкв\b|\bкв\.|\bкварти", q):
            desired_unit_types = ["apartment", "квартира"]
        elif re.search(r"паркомісц|паркінг|парков", q):
            desired_unit_types = ["parking", "паркомісце", "паркінг"]
        elif re.search(r"комор|кладов", q):
            desired_unit_types = ["storage", "комора", "кладова"]

        sql_lower = plan.structured_query.lower()
        if desired_unit_types and "unit_type" not in sql_lower:
            # Try to qualify unit_type with the main FROM alias if present.
            alias = None
            m = re.search(r"\bfrom\s+(unit_residents|units_extended|units)\s+([a-zA-Z_]\w*)\b", sql_lower)
            if m:
                alias = m.group(2)
            # Normalize stored values on the fly (case/whitespace tolerant).
            col = f"{alias}.unit_type" if alias else "unit_type"
            cond = f"lower(trim({col})) = ANY(:unit_types)"

            if " where " in sql_lower:
                plan.structured_query = re.sub(
                    r"\bwhere\b",
                    f"WHERE {cond} AND",
                    plan.structured_query,
                    flags=re.IGNORECASE,
                )
            else:
                match = re.search(r"\b(group by|order by|limit)\b", sql_lower)
                if match:
                    idx = match.start()
                    plan.structured_query = plan.structured_query[:idx] + f" WHERE {cond} " + plan.structured_query[idx:]
                else:
                    plan.structured_query = plan.structured_query + f" WHERE {cond}"

            plan.structured_params = dict(plan.structured_params or {})
            plan.structured_params["unit_types"] = [t.strip().lower() for t in desired_unit_types]

        # ------------------------------------------------------------------
        # Resident address default: "де живе X / де він живе" зазвичай означає
        # квартиру. Якщо користувач не просить явно інші типи приміщень або "всі",
        # обмежуємо результат житловими приміщеннями.
        # ------------------------------------------------------------------
        if getattr(plan, "intent", None) == "resident_address":
            sql_lower = plan.structured_query.lower()
            has_unit_type_filter = "unit_type" in sql_lower

            wants_other_types = bool(
                re.search(r"паркомісц|паркінг|комор|кладов|нежитл|підвал|усі|всі|все майно|усе майно|об'єкти|об’єкти", q)
            )

            if not wants_other_types and not has_unit_type_filter:
                alias = None
                m = re.search(r"\bfrom\s+(unit_residents|units_extended|units)\s+([a-zA-Z_]\w*)\b", sql_lower)
                if m:
                    alias = m.group(2)
                col = f"{alias}.unit_type" if alias else "unit_type"
                cond = f"lower(trim({col})) = ANY(:unit_types)"

                if " where " in sql_lower:
                    plan.structured_query = re.sub(
                        r"\bwhere\b",
                        f"WHERE {cond} AND",
                        plan.structured_query,
                        flags=re.IGNORECASE,
                    )
                else:
                    match = re.search(r"\b(group by|order by|limit)\b", sql_lower)
                    if match:
                        idx = match.start()
                        plan.structured_query = plan.structured_query[:idx] + f" WHERE {cond} " + plan.structured_query[idx:]
                    else:
                        plan.structured_query = plan.structured_query + f" WHERE {cond}"

                plan.structured_params = dict(plan.structured_params or {})
                plan.structured_params["unit_types"] = ["apartment", "квартира"]
            elif not wants_other_types and has_unit_type_filter:
                # Even if planner added unit_type filter, force it to apartments only,
                # unless user explicitly asked for other premises.
                plan.structured_params = dict(plan.structured_params or {})
                plan.structured_params.pop("unit_type", None)
                plan.structured_params["unit_types"] = ["apartment", "квартира"]

        return plan