from app.services.validation_agent import ValidationAgent


data = {
    "patient_name": "John Doe",
    "member_id": "M12345",
    "provider_name": "ABC Hospital",
    "diagnosis": "Headache",
    "diagnosis_code": "R51",
    "procedure_code": "70551",
    "requested_treatment": "MRI brain",
    "clinical_complaint": "Patient has persistent headache.",
    "clinical_findings": "Persistent headache; neurologic examination not documented.",
    "previous_treatment": "",
}


deterministic_result = {
    "valid": True,
    "missing_fields": [],
    "present_fields": [
        "patient_name",
        "member_id",
        "provider_name",
        "diagnosis_code",
        "procedure_code",
    ],
}


agent = ValidationAgent()

result = agent.validate(
    extracted_data=data,
    deterministic_result=deterministic_result,
)


print("\n==============================")
print("VALIDATION AGENT RESULT")
print("==============================")
print(result)
