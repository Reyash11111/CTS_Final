from typing import Any, Dict, List


REQUIRED_FIELDS = [
    "patient_name",
    "member_id",
    "provider_name",
    "diagnosis_code",
    "procedure_code",
]


def deterministic_validate(data: Dict[str, Any]) -> Dict[str, Any]:

    missing_fields: List[str] = []
    present_fields: List[str] = []

    for field in REQUIRED_FIELDS:

        value = data.get(field)

        if value is None or str(value).strip() == "":
            missing_fields.append(field)
        else:
            present_fields.append(field)

    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "present_fields": present_fields,
    }