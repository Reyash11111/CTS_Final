def predict_hospital_pa(features: dict):

    criteria = []

    def add(code, label, passed, observed, weight):
        criteria.append({
            "code": code,
            "label": label,
            "passed": bool(passed),
            "observed": observed,
            "weight": weight,
        })

    # ---------------------------------------------------------
    # 1. Diagnosis
    # ---------------------------------------------------------

    diagnosis_ok = bool(
        features.get("diagnosis")
    )

    add(
        "DX",
        "Diagnosis documented",
        diagnosis_ok,
        features.get("diagnosis"),
        0.15,
    )

    # ---------------------------------------------------------
    # 2. ICD-10
    # ---------------------------------------------------------

    icd_ok = bool(
        features.get("diagnosis_code")
    )

    add(
        "ICD",
        "ICD-10 code documented",
        icd_ok,
        features.get("diagnosis_code"),
        0.10,
    )

    # ---------------------------------------------------------
    # 3. Clinical complaint
    # ---------------------------------------------------------

    complaint_ok = bool(
        features.get("clinical_complaint")
    )

    add(
        "CLINICAL",
        "Clinical complaint documented",
        complaint_ok,
        features.get("clinical_complaint"),
        0.10,
    )

    # ---------------------------------------------------------
    # 4. Clinical findings
    # ---------------------------------------------------------

    findings = (
        features.get("clinical_findings")
        or ""
    )

    findings_ok = bool(findings.strip())

    add(
        "FINDINGS",
        "Relevant clinical findings documented",
        findings_ok,
        findings[:200],
        0.15,
    )

    # ---------------------------------------------------------
    # 5. Imaging
    # ---------------------------------------------------------

    imaging_ok = bool(
        features.get("imaging_present")
    )

    add(
        "IMAGING",
        "Diagnostic/imaging evidence available",
        imaging_ok,
        "Attached" if imaging_ok else "Missing",
        0.15,
    )

    # ---------------------------------------------------------
    # 6. Clinical rationale
    # ---------------------------------------------------------

    rationale_ok = bool(
        features.get("clinical_rationale")
    )

    add(
        "RATIONALE",
        "Medical necessity rationale documented",
        rationale_ok,
        (
            features.get("clinical_rationale") or
            "Missing"
        )[:200],
        0.10,
    )

    # ---------------------------------------------------------
    # 7. Procedure
    # ---------------------------------------------------------

    procedure_ok = bool(
        features.get("requested_treatment")
    )

    cpt_ok = bool(
        features.get("procedure_code")
    )

    procedure_pass = procedure_ok and cpt_ok

    add(
        "PROCEDURE",
        "Requested procedure and CPT documented",
        procedure_pass,
        (
            f"{features.get('requested_treatment')} "
            f"(CPT {features.get('procedure_code')})"
        ),
        0.10,
    )

    # ---------------------------------------------------------
    # 8. Documentation
    # ---------------------------------------------------------

    doc_count = int(
        features.get(
            "supporting_documents_count",
            0
        ) or 0
    )

    documentation_ok = doc_count >= 5

    add(
        "DOC",
        "Supporting documentation is sufficiently complete",
        documentation_ok,
        f"{doc_count} supporting documents",
        0.10,
    )

    # ---------------------------------------------------------
    # 9. Network status
    # ---------------------------------------------------------

    network_ok = (
        features.get("facility_status")
        == "In-Network"
    )

    add(
        "NETWORK",
        "Facility is in-network",
        network_ok,
        features.get("facility_status"),
        0.05,
    )

    # ---------------------------------------------------------
    # SCORE
    # ---------------------------------------------------------

    total_weight = sum(
        c["weight"]
        for c in criteria
    )

    score = sum(
        c["weight"]
        for c in criteria
        if c["passed"]
    ) / total_weight

    score = round(score, 4)

    failed = [
        c["label"]
        for c in criteria
        if not c["passed"]
    ]

    # ---------------------------------------------------------
    # DECISION
    # ---------------------------------------------------------

    if score >= 0.80:

        decision = "APPROVED"
        status = "AUTO_APPROVED"

        rationale = (
            "The uploaded hospital prior-authorization packet "
            "contains sufficient clinical evidence, diagnosis "
            "coding, procedure information and supporting "
            "documentation for an approval recommendation."
        )

        confidence = min(
            0.99,
            round(0.70 + score * 0.25, 3)
        )

    elif score >= 0.55:

        decision = None
        status = "PENDING_REVIEW"

        rationale = (
            "The request contains partially sufficient evidence "
            "but requires clinical reviewer validation. "
            + (
                "Missing or weak evidence: "
                + ", ".join(failed[:3])
                if failed
                else ""
            )
        )

        confidence = round(
            0.60 + abs(score - 0.55) * 0.3,
            3
        )

    else:

        decision = "DENIED"
        status = "AUTO_DENIED"

        rationale = (
            "The submitted packet does not contain sufficient "
            "supporting evidence for an automatic approval "
            "recommendation."
        )

        confidence = round(
            min(0.95, 0.70 + (1 - score) * 0.25),
            3
        )

    return {
        "decision": decision,
        "status": status,
        "necessity_score": score,
        "policy_fit_score": score,
        "confidence": confidence,
        "rationale": rationale,
        "criteria": criteria,
        "prediction_type": "HOSPITAL_PA_RULE_ENGINE",
    }