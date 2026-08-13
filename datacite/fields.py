#Returns list of dictionary values of field of a certain type
def compound_rows(fields: list[dict], type_name: str) -> list[dict]:
    if not fields:
        return []

    target_field = next((field for field in fields if field.get("typeName", "") == type_name), None)
    if target_field is None:
        return []

    value = target_field.get("value", None)

    if not isinstance(value, list):
        return []

    return value

#Returns singular value of field of a certain type
def singular_value(fields: list[dict], type_name: str) -> str | None:
    if not fields:
        return None

    target_field = next((field for field in fields if field.get("typeName", "") == type_name), None)
    if target_field is None:
        return None

    value = target_field.get("value", None)

    return value

def list_values(fields: list[dict], type_name: str) -> list[str]:
    if not fields:
        return []

    target_field = next((field for field in fields if field.get("typeName", "") == type_name), None)
    if target_field is None:
        return []

    value = target_field.get("value", None)

    if not isinstance(value, list):
        return []

    return value

def child_value(row: dict, type_name: str) -> str | None:
    child_field = row.get(type_name)
    if child_field is None:
        return None

    value = child_field.get("value")

    if isinstance(value, list):
        return value[0] if value else None

    return value

