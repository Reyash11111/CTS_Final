import re


def clean(value):
    if value is None:
        return None

    value = re.sub(r"\s+", " ", str(value))
    value = value.strip(" :-|")

    return value if value else None


def label(text, pattern):
    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.MULTILINE
    )

    if not match:
        return None

    return clean(match.group(1))


def checkbox(text, pattern):
    return bool(
        re.search(
            pattern,
            text,
            re.IGNORECASE
        )
    )


def extract_hospital_pa(text):

    fields = {}

    # =========================================================
    # PATIENT / MEMBER
    # =========================================================

    fields["patient_name"] = label(
        text,
        r"^Patient Name\s+(.+)$"
    )

    fields["member_id"] = label(
        text,
        r"^Member ID\s+(\S+)"
    )

    fields["date_of_birth"] = label(
        text,
        r"Date of Birth:\s*([0-9 /]+)"
    )

    age_match = re.search(
        r"Gender\s*/\s*Age.*?Age:\s*(\d+)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    fields["age"] = (
        int(age_match.group(1))
        if age_match
        else None
    )

    if checkbox(
        text,
        r"Gender\s*/\s*Age.*?\[X\]\s*Female"
    ):
        fields["sex"] = "F"

    elif checkbox(
        text,
        r"Gender\s*/\s*Age.*?\[X\]\s*Male"
    ):
        fields["sex"] = "M"

    elif checkbox(
        text,
        r"Gender\s*/\s*Age.*?\[X\]\s*Other"
    ):
        fields["sex"] = "Other"

    fields["mobile_email"] = label(
        text,
        r"^Mobile / Email\s+(.+)$"
    )

    fields["policy_group"] = label(
        text,
        r"^Policy / Group\s+(.+)$"
    )

    fields["primary_care_provider"] = label(
        text,
        r"^Primary Care Provider\s+(.+)$"
    )

    # =========================================================
    # PROVIDER / HOSPITAL
    # =========================================================

    fields["treating_provider"] = label(
        text,
        r"^Treating Provider\s+(.+)$"
    )

    fields["provider_contact"] = label(
        text,
        r"^Provider Contact\s+(.+)$"
    )

    fields["hospital_facility"] = label(
        text,
        r"^Hospital / Facility\s+(.+)$"
    )

    fields["facility_status"] = (
        "In-Network"
        if checkbox(
            text,
            r"Facility Status.*?\[X\]\s*In-Network"
        )
        else "Out-of-Network"
    )

    fields["hospital_contact"] = label(
        text,
        r"^Hospital Contact\s+(.+)$"
    )

    # =========================================================
    # CLINICAL INFORMATION
    # =========================================================

    fields["clinical_complaint"] = label(
        text,
        r"^Clinical Complaint\s+(.+)$"
    )

    fields["clinical_findings"] = label(
        text,
        r"^Relevant Clinical Findings\s+(.+)$"
    )

    fields["past_history"] = label(
        text,
        r"^Past / Relevant History\s+(.+)$"
    )

    duration = label(
        text,
        r"^Duration of Present Condition\s+(\d+)\s+days"
    )

    fields["condition_duration_days"] = (
        int(duration)
        if duration
        else None
    )

    fields["first_consultation"] = label(
        text,
        r"^Date of First Consultation\s+(.+)$"
    )

    fields["diagnosis"] = label(
        text,
        r"^Primary / Provisional Diagnosis\s+(.+)$"
    )

    fields["diagnosis_code"] = label(
        text,
        r"^ICD-10 Code\s+([A-Z0-9.]+)"
    )

    fields["additional_diagnosis"] = label(
        text,
        r"^Additional Diagnosis / Comorbidities\s+(.+)$"
    )

    fields["clinical_rationale"] = label(
        text,
        r"Clinical Rationale / Necessity\s+(.+?)"
        r"(?=\s+PROPOSED TREATMENT / PROCEDURE)"
    )

    # Because the rationale can wrap onto multiple lines
    if not fields["clinical_rationale"]:

        match = re.search(
            r"Clinical Rationale / Necessity\s+"
            r"(.+?)"
            r"\s+PROPOSED TREATMENT / PROCEDURE",
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            fields["clinical_rationale"] = clean(
                match.group(1)
            )

    # =========================================================
    # PROCEDURE
    # =========================================================

    if checkbox(
        text,
        r"Treatment Type.*?\[X\]\s*Surgical"
    ):
        fields["treatment_type"] = "Surgical"

    elif checkbox(
        text,
        r"Treatment Type.*?\[X\]\s*Medical Management"
    ):
        fields["treatment_type"] = "Medical Management"

    elif checkbox(
        text,
        r"Treatment Type.*?\[X\]\s*ICU"
    ):
        fields["treatment_type"] = "ICU"

    elif checkbox(
        text,
        r"Treatment Type.*?\[X\]\s*Investigation"
    ):
        fields["treatment_type"] = "Investigation"

    fields["requested_treatment"] = label(
        text,
        r"^Treatment / Procedure\s+(.+)$"
    )

    fields["procedure_code"] = label(
        text,
        r"^Procedure Code\s+CPT:\s*(\S+)"
    )

    fields["treatment_details"] = label(
        text,
        r"^Treatment Details\s+(.+)$"
    )

    fields["medication_therapy"] = label(
        text,
        r"^Medication / Therapy\s+(.+)$"
    )

    if checkbox(
        text,
        r"Route of Administration.*?\[X\]\s*IV"
    ):
        fields["route"] = "IV"

    elif checkbox(
        text,
        r"Route of Administration.*?\[X\]\s*Oral"
    ):
        fields["route"] = "Oral"

    elif checkbox(
        text,
        r"Route of Administration.*?\[X\]\s*IM"
    ):
        fields["route"] = "IM"

    # =========================================================
    # HOSPITALIZATION
    # =========================================================

    fields["admission_datetime"] = label(
        text,
        r"^Admission Date / Time\s+(.+)$"
    )

    if checkbox(
        text,
        r"Hospitalization Type.*?\[X\]\s*Emergency"
    ):
        fields["hospitalization_type"] = "Emergency"

    elif checkbox(
        text,
        r"Hospitalization Type.*?\[X\]\s*Planned"
    ):
        fields["hospitalization_type"] = "Planned"

    elif checkbox(
        text,
        r"Hospitalization Type.*?\[X\]\s*Day Care"
    ):
        fields["hospitalization_type"] = "Day Care"

    elif checkbox(
        text,
        r"Hospitalization Type.*?\[X\]\s*Maternity"
    ):
        fields["hospitalization_type"] = "Maternity"

    los = label(
        text,
        r"^Expected Length of Stay\s+(\d+)\s+days"
    )

    fields["expected_length_of_stay_days"] = (
        int(los) if los else None
    )

    icu = label(
        text,
        r"^Expected ICU Stay\s+(\d+)\s+days"
    )

    fields["expected_icu_stay_days"] = (
        int(icu) if icu else None
    )

    fields["room_level_of_care"] = label(
        text,
        r"^Room / Level of Care\s+(.+)$"
    )

    # =========================================================
    # INCIDENT / LEGAL
    # =========================================================

    fields["accident_injury"] = (
        "No"
        if checkbox(
            text,
            r"Accident / Injury.*?\[X\]\s*No"
        )
        else "Yes"
    )

    fields["rta"] = (
        "No"
        if checkbox(
            text,
            r"RTA / Medico-Legal RTA:\s*\[X\]\s*No"
        )
        else "Yes"
    )

    fields["medico_legal"] = (
        "No"
        if checkbox(
            text,
            r"Medico-Legal:\s*\[X\]\s*No"
        )
        else "Yes"
    )

    fields["police_fir"] = (
        "No"
        if checkbox(
            text,
            r"Police / FIR.*?\[X\]\s*No"
        )
        else "Yes"
    )

    fields["substance_related_injury"] = (
        "No"
        if checkbox(
            text,
            r"Substance-Related Injury.*?\[X\]\s*No"
        )
        else "Yes"
    )

    # =========================================================
    # COST
    # =========================================================

    cost_labels = [
        "Room + Nursing + Diet",
        "Investigation / Diagnostics",
        "ICU Charges",
        "OT / Procedure Charges",
        "Professional Fees",
        "Medicines / Consumables",
        "Implants",
        "Other Hospital Expenses",
        "Package Charges",
        "TOTAL EXPECTED COST",
    ]

    for cost_label in cost_labels:

        key = (
            cost_label.lower()
            .replace("+", "plus")
            .replace("/", "_")
            .replace(" ", "_")
        )

        value = label(
            text,
            rf"^{re.escape(cost_label)}\s+(.+)$"
        )

        fields[key] = value

    # =========================================================
    # SUPPORTING DOCUMENTS
    # =========================================================

    document_fields = {
        "clinical_records_attached":
            "Clinical Records",

        "diagnostic_lab_reports_attached":
            "Diagnostic / Lab Reports",

        "imaging_reports_attached":
            "Imaging Reports",

        "prescription_treatment_order_attached":
            "Prescription / Treatment Order",

        "previous_medical_records_attached":
            "Previous Relevant Medical Records",

        "procedure_surgical_documentation_attached":
            "Procedure / Surgical Documentation",

        "cost_estimate_attached":
            "Cost Estimate",
    }

    for key, document_name in document_fields.items():

        fields[key] = checkbox(
            text,
            rf"{re.escape(document_name)}\s+\[X\]\s*Attached"
        )

    fields["supporting_documents_count"] = sum(
        1
        for key in document_fields
        if fields[key]
    )

    fields["other_supporting_documents"] = label(
        text,
        r"^Other\s+(.+)$"
    )

    # =========================================================
    # REQUEST
    # =========================================================

    fields["authorization_requested_for"] = label(
        text,
        r"^Authorization Requested For\s+(.+)$"
    )

    fields["requested_service_date"] = label(
        text,
        r"^Requested Service Date\s+(.+)$"
    )

    fields["treating_provider_signature"] = label(
        text,
        r"^Treating Provider Signature\s+(.+)$"
    )

    fields["hospital_authorized_signature"] = label(
        text,
        r"^Hospital Authorized Signature\s+(.+)$"
    )

    fields["hospital_provider_stamp"] = label(
        text,
        r"^Hospital / Provider Stamp\s+(.+)$"
    )

    # =========================================================
    # DERIVED FIELDS FOR EXISTING APP
    # =========================================================

    fields["comorbidities"] = (
        fields.get("additional_diagnosis")
        or "None"
    )

    fields["imaging_present"] = int(
        fields.get("imaging_reports_attached", False)
        or
        "ultrasound" in (
            fields.get("clinical_findings") or ""
        ).lower()
        or
        "imaging" in text.lower()
    )

    fields["lab_results_present"] = int(
        fields.get("diagnostic_lab_reports_attached", False)
    )

    fields["doctor_note_present"] = int(
        bool(fields.get("clinical_complaint"))
        and
        bool(fields.get("clinical_findings"))
    )

    fields["medication_history_present"] = int(
        bool(fields.get("medication_therapy"))
    )

    fields["documentation_complete"] = int(
        fields["supporting_documents_count"] >= 5
    )

    # These are kept only for compatibility with the old schema.
    fields["member_eligible"] = 1
    fields["treatment_covered"] = int(
        fields.get("facility_status") == "In-Network"
    )

    fields["provider_specialty"] = "Surgery"
    fields["provider_type"] = "Hospital"

    fields["payer"] = "Northstar Health Insurance"

    fields["document_type"] = "HOSPITAL_PA"

    fields["_patient_name"] = fields.get("patient_name")
    fields["_mrn"] = fields.get("member_id")

    return fields
