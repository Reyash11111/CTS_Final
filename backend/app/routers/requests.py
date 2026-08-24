import shutil
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..database import get_db
from ..models import (
    Appeal,
    AuditEvent,
    AuthRequest,
    Document,
    Patient,
    User,
)

from ..schemas import AppealCreate, RequestCreate
from ..security import current_user, require_provider
from ..services import ml, routing
from ..services.pdf_extract import extract_from_file
from ..services.pipeline import adjudicate, log
from ..services import validation_agent as validation_agent_service
from ..services import critic_agent as critic_agent_service
from ..services.vocab import DIAGNOSIS_CODES


router = APIRouter(
    prefix="/api",
    tags=["requests"],
)


# ============================================================
# REQUIRED FIELDS
# ============================================================

REQUIRED = [
    "patient_name",
    "age",
    "sex",
    "diagnosis",
    "diagnosis_code",
    "clinical_complaint",
    "clinical_findings",
    "requested_treatment",
    "procedure_code",
    "treatment_type",
    "hospital_facility",
    "payer",
    "supporting_documents_count",
]


LEGACY_REQUIRED = [
    "age",
    "sex",
    "bmi",
    "diagnosis",
    "disease_severity",
    "symptom_burden_0_10",
    "symptom_duration_months",
    "requested_treatment",
    "dose_category",
    "frequency",
    "route",
    "requested_duration_months",
    "request_reason",
    "previous_treatment_count",
    "previous_failed_count",
    "previous_partial_response_count",
    "previous_adverse_effect_count",
    "longest_previous_treatment_weeks",
    "provider_specialty",
    "provider_state",
    "provider_type",
    "payer",
]


# ============================================================
# HUMAN REVIEW PRIORITY
# ============================================================

SEVERITY_MAP = {
    "critical": 0.95,
    "life threatening": 0.98,
    "life-threatening": 0.98,
    "emergency": 0.98,
    "unstable": 0.95,
    "severe": 0.85,
    "high": 0.75,
    "moderate": 0.55,
    "medium": 0.55,
    "mild": 0.30,
    "low": 0.20,
    "routine": 0.15,
}


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert values such as:

        0.95
        95
        "95%"
        "0.95"

    into a normalized 0-1 value.
    """

    if value is None:
        return default

    try:
        if isinstance(value, str):
            cleaned = value.strip().replace("%", "")
            number = float(cleaned)
        else:
            number = float(value)

        if number > 1:
            number = number / 100

        return max(
            0.0,
            min(1.0, number),
        )

    except (TypeError, ValueError):
        return default


def _severity_from_text(
    value: Any,
) -> float:
    """
    Convert textual clinical severity into a 0-1 score.
    """

    if value is None:
        return 0.0

    text = str(value).strip().lower()

    if not text:
        return 0.0

    for label, score in SEVERITY_MAP.items():
        if label in text:
            return score

    return 0.0


def _calculate_human_review_priority(
    features: dict,
    validation: dict,
) -> dict:
    """
    Calculate human-review priority.

    Priority:

        CRITICAL >= 0.85
        HIGH     >= 0.70
        MEDIUM   >= 0.50
        LOW      < 0.50

    Severity is the primary factor.
    Urgent clinical wording can increase severity.
    """

    # --------------------------------------------------------
    # 1. Explicit severity score
    # --------------------------------------------------------

    severity_score = 0.0

    explicit_candidates = [
        validation.get("severity_score"),
        validation.get("clinical_severity_score"),
        features.get("severity_score"),
        features.get("clinical_severity_score"),
    ]

    for candidate in explicit_candidates:
        value = _safe_float(
            candidate,
            0.0,
        )

        if value > 0:
            severity_score = value
            break

    # --------------------------------------------------------
    # 2. Text severity
    # --------------------------------------------------------

    if severity_score == 0:
        textual_candidates = [
            validation.get("clinical_severity"),
            validation.get("severity"),
            features.get("clinical_severity"),
            features.get("disease_severity"),
            features.get("severity"),
        ]

        for candidate in textual_candidates:
            value = _severity_from_text(candidate)

            if value > 0:
                severity_score = value
                break

    # --------------------------------------------------------
    # 3. Symptom burden
    # --------------------------------------------------------

    raw_burden = features.get(
        "symptom_burden_0_10"
    )

    if raw_burden is not None:
        try:
            burden_text = (
                str(raw_burden)
                .replace("/10", "")
                .strip()
            )

            burden = float(burden_text)

            burden = max(
                0.0,
                min(
                    10.0,
                    burden,
                ),
            )

            symptom_score = burden / 10.0

            if severity_score == 0:
                severity_score = symptom_score

        except (TypeError, ValueError):
            pass

    # --------------------------------------------------------
    # 4. Urgent clinical indicators
    # --------------------------------------------------------

    combined_text = " ".join(
        [
            str(
                features.get("diagnosis")
                or ""
            ),
            str(
                features.get("clinical_complaint")
                or ""
            ),
            str(
                features.get("clinical_findings")
                or ""
            ),
            str(
                features.get("requested_treatment")
                or ""
            ),
            str(
                features.get("disease_severity")
                or ""
            ),
        ]
    ).lower()

    urgent_terms = [
        "emergency",
        "critical",
        "life threatening",
        "life-threatening",
        "acute deterioration",
        "unstable",
        "severe bleeding",
        "respiratory distress",
        "chest pain",
        "stroke",
        "sepsis",
        "organ failure",
        "focal neurological deficit",
        "focal neurologic deficit",
        "neurological deficit",
        "neurologic deficit",
        "acute neurological",
        "acute neurologic",
    ]

    urgent_signal = any(
        term in combined_text
        for term in urgent_terms
    )

    if urgent_signal:
        severity_score = max(
            severity_score,
            0.90,
        )

    # --------------------------------------------------------
    # 5. Default severity
    # --------------------------------------------------------

    if severity_score == 0:
        severity_score = 0.30

    severity_score = max(
        0.0,
        min(
            1.0,
            severity_score,
        ),
    )

    # --------------------------------------------------------
    # 6. Priority
    # --------------------------------------------------------

    if severity_score >= 0.85:
        priority = "CRITICAL"
        sla = "Immediate human review"

    elif severity_score >= 0.70:
        priority = "HIGH"
        sla = "Review as soon as possible"

    elif severity_score >= 0.50:
        priority = "MEDIUM"
        sla = "Review within normal queue"

    else:
        priority = "LOW"
        sla = "Routine review"

    # --------------------------------------------------------
    # 7. Return priority information
    # --------------------------------------------------------

    return {
        "severity_score": round(
            severity_score,
            4,
        ),
        "clinical_severity": priority,
        "review_priority": priority,
        "priority_label": priority,
        "sla": sla,
        "priority_reason": (
            "Human-review priority is calculated "
            "primarily from clinical severity and "
            "urgent clinical indicators."
        ),
    }


def _apply_human_review_priority(
    features: dict,
    validation: dict,
) -> dict:
    """
    Merge severity and priority into the
    validation-agent result.
    """

    priority = _calculate_human_review_priority(
        features,
        validation,
    )

    return {
        **validation,
        **priority,
    }


# ============================================================
# VALIDATION AGENT ADAPTER
# ============================================================

def _call_validation_agent(
    features: dict,
    document_text: str,
) -> dict:
    """
    Safely call the validation service.

    This intentionally does NOT use:

        from ..services.validation_agent import run_validation_agent

    because that function is currently missing in your
    validation_agent.py and was causing the application
    startup ImportError.

    It supports common function names if your service
    already exposes one.
    """

    candidate_names = [
        "run_validation_agent",
        "validate_request",
        "run_agent",
        "validate",
    ]

    for function_name in candidate_names:
        function = getattr(
            validation_agent_service,
            function_name,
            None,
        )

        if callable(function):
            try:
                result = function(
                    features=features,
                    document_text=document_text,
                )
            except TypeError:
                try:
                    result = function(
                        features,
                        document_text,
                    )
                except TypeError:
                    result = function(features)

            if isinstance(result, dict):
                return result

    # --------------------------------------------------------
    # Deterministic fallback
    # --------------------------------------------------------
    #
    # This prevents the whole API from crashing if the
    # validation-agent function is not exposed.
    #
    # It also guarantees that missing documentation /
    # severe clinical cases can enter human review.
    # --------------------------------------------------------

    missing_context = []
    documentation_needed = []
    inconsistencies = []

    required_validation_fields = [
        "diagnosis",
        "clinical_complaint",
        "clinical_findings",
        "requested_treatment",
        "procedure_code",
    ]

    for field in required_validation_fields:
        value = features.get(field)

        if value in (
            None,
            "",
            "Unknown",
        ):
            missing_context.append(
                f"{field.replace('_', ' ').title()} "
                "is missing."
            )

    supporting_count = features.get(
        "supporting_documents_count"
    )

    try:
        supporting_count = int(
            supporting_count or 0
        )
    except (TypeError, ValueError):
        supporting_count = 0

    if supporting_count == 0:
        documentation_needed.append(
            "Supporting clinical documentation "
            "should be reviewed."
        )

    disease_severity = str(
        features.get("disease_severity")
        or ""
    ).lower()

    urgent_words = [
        "critical",
        "emergency",
        "severe",
        "life threatening",
        "life-threatening",
        "unstable",
    ]

    urgent = any(
        word in disease_severity
        for word in urgent_words
    )

    human_required = bool(
        missing_context
        or documentation_needed
        or inconsistencies
        or urgent
    )

    return {
        "contextually_complete": not bool(
            missing_context
        ),
        "consistency_check": (
            "WARNING"
            if inconsistencies
            else "PASS"
        ),
        "missing_context": missing_context,
        "inconsistencies": inconsistencies,
        "documentation_needed": documentation_needed,
        "reasoning": (
            "Deterministic validation fallback was used "
            "because no compatible validation-agent "
            "function was exposed by validation_agent.py."
        ),
        "human_review_required": human_required,
        "confidence": 0.60,
    }
# ============================================================
# CRITIC AGENT ADAPTER
# ============================================================

def _call_critic_agent(
    features: dict,
    validation_result: dict,
    document_text: str = "",
) -> dict:
    """
    Run the second agent against the output of the
    primary validation agent.

    The critic does NOT replace the validation agent.
    It checks whether the validation agent produced a
    structurally and logically valid result.
    """

    function = getattr(
        critic_agent_service,
        "run_critic_agent",
        None,
    )

    if not callable(function):
        return {
            "status": "ERROR",
            "agent_working": False,
            "score": 0.0,
            "issues": [
                "Critic agent function is unavailable."
            ],
            "reasoning": (
                "The primary validation agent result "
                "could not be independently verified."
            ),
            "mode": "unavailable",
        }

    try:

        result = function(
            features=features,
            validation_result=validation_result,
            document_text=document_text,
        )

        if isinstance(result, dict):
            return result

        return {
            "status": "ERROR",
            "agent_working": False,
            "score": 0.0,
            "issues": [
                "Critic agent returned an invalid result."
            ],
            "reasoning": (
                "The critic agent did not return a dictionary."
            ),
            "mode": "error",
        }

    except Exception as exc:

        print(
            "[CRITIC AGENT ERROR]",
            exc,
        )

        return {
            "status": "ERROR",
            "agent_working": False,
            "score": 0.0,
            "issues": [
                "Critic agent could not verify the validation agent."
            ],
            "reasoning": (
                "Independent verification of the "
                "validation agent failed."
            ),
            "agent_error": str(exc),
            "mode": "error",
        }

# ============================================================
# DOCUMENT UPLOAD
# ============================================================

@router.post(
    "/documents/upload",
    status_code=201,
)
def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(require_provider),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Upload a PDF. Other formats are not read by the extractor.",
        )

    stored = (
        UPLOAD_DIR
        / f"{uuid.uuid4().hex}.pdf"
    )

    try:
        with stored.open("wb") as fh:
            shutil.copyfileobj(
                file.file,
                fh,
            )

        result = extract_from_file(
            stored
        )

    except Exception as exc:
        stored.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Could not read this PDF: {exc}",
        )

    if result["char_count"] < 50:
        stored.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            (
                "No selectable text found. "
                "This looks like a scanned image. "
                "Run OCR on it first, then upload again."
            ),
        )

    fields = result["fields"]

    doc = Document(
        request_id=None,
        uploaded_by=user.id,
        filename=filename,
        stored_path=str(stored),
        page_count=result["page_count"],
        char_count=result["char_count"],
        extraction_confidence=result["confidence"],
        extracted_fields=fields,
        unmatched_fields=result["unmatched"],
        raw_text=result["raw_text"],
    )

    db.add(doc)
    db.flush()

    log(
        db,
        "DOCUMENT_UPLOADED",
        actor=user,
        detail={
            "document_id": doc.id,
            "filename": filename,
            "pages": result["page_count"],
            "confidence": result["confidence"],
            "unmatched_count": len(
                result["unmatched"]
            ),
        },
    )

    db.commit()

    still_missing = [
        field
        for field in REQUIRED
        if fields.get(field) in (
            None,
            "",
        )
    ]

    return {
        "document_id": doc.id,
        "filename": filename,
        "page_count": result["page_count"],
        "char_count": result["char_count"],
        "extraction_confidence": result["confidence"],
        "fields": {
            key: value
            for key, value in fields.items()
            if not key.startswith("_")
        },
        "patient_name": fields.get(
            "_patient_name"
        ),
        "mrn": fields.get(
            "_mrn"
        ),
        "missing_required": still_missing,
    }


# ============================================================
# CREATE PRIOR AUTHORIZATION REQUEST
# ============================================================

@router.post(
    "/requests",
    status_code=201,
)
def create_request(
    body: RequestCreate,
    user: User = Depends(require_provider),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # 1. Features
    # --------------------------------------------------------

    features = dict(
        body.features or {}
    )

    # --------------------------------------------------------
    # 2. Resolve diagnosis code
    # --------------------------------------------------------

    if not features.get(
        "diagnosis_code"
    ):
        diagnosis = features.get(
            "diagnosis"
        )

        if diagnosis:
            features["diagnosis_code"] = (
                DIAGNOSIS_CODES.get(
                    diagnosis
                )
            )

    # --------------------------------------------------------
    # 3. Required field validation
    # --------------------------------------------------------

    missing = [
        field
        for field in REQUIRED
        if features.get(field) in (
            None,
            "",
        )
    ]

    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            (
                "Fill in these fields before submitting: "
                + ", ".join(missing)
            ),
        )

    # --------------------------------------------------------
    # 4. Defaults
    # --------------------------------------------------------

    features.setdefault(
        "comorbidities",
        "Unknown",
    )

    for flag in (
        "doctor_note_present",
        "lab_results_present",
        "imaging_present",
        "medication_history_present",
        "documentation_complete",
        "member_eligible",
        "treatment_covered",
    ):
        features[flag] = int(
            features.get(
                flag,
                0,
            )
            or 0
        )

    # --------------------------------------------------------
    # 5. Create patient
    # --------------------------------------------------------

    patient = None

    patient_name = (
        body.patient_name
        or features.get(
            "patient_name"
        )
    )

    mrn = (
        body.mrn
        or features.get(
            "mrn"
        )
    )

    if patient_name or mrn:
        patient = Patient(
            organization_id=user.organization_id,
            mrn=mrn,
            full_name=patient_name,
            age=features.get(
                "age"
            ),
            sex=features.get(
                "sex"
            ),
        )

        db.add(patient)
        db.flush()

    # --------------------------------------------------------
    # 6. Create request
    # --------------------------------------------------------

    count = (
        db.query(
            AuthRequest
        ).count()
        + 1
    )

    req = AuthRequest(
        case_number=(
            f"PA-{datetime.now(timezone.utc):%Y%m}"
            f"-{count:06d}"
        ),
        organization_id=user.organization_id,
        created_by=user.id,
        patient_id=(
            patient.id
            if patient
            else None
        ),
        features=features,
        status="SUBMITTED",
    )

    db.add(req)
    db.flush()

    # --------------------------------------------------------
    # 7. Audit submission
    # --------------------------------------------------------

    log(
        db,
        "REQUEST_SUBMITTED",
        request_id=req.id,
        actor=user,
        detail={
            "case_number": req.case_number,
            "diagnosis": features.get(
                "diagnosis"
            ),
            "treatment": features.get(
                "requested_treatment"
            ),
        },
    )

    # --------------------------------------------------------
    # 8. Link document
    # --------------------------------------------------------

    if body.document_id:
        doc = db.get(
            Document,
            body.document_id,
        )

        if (
            doc
            and doc.uploaded_by == user.id
        ):
            doc.request_id = req.id

    db.flush()

    # --------------------------------------------------------
    # 9. AI / contextual validation
    # --------------------------------------------------------

    docs = (
        db.query(Document)
        .filter(
            Document.request_id
            == req.id
        )
        .all()
    )

    document_text = "\n\n".join(
        doc.raw_text
        for doc in docs
        if doc.raw_text
    )

    try:
        validation_result = (
            _call_validation_agent(
                features=features,
                document_text=document_text,
            )
        )

    except Exception as exc:
        validation_result = {
            "contextually_complete": False,
            "consistency_check": "ERROR",
            "missing_context": [],
            "inconsistencies": [
                "Validation agent failed."
            ],
            "documentation_needed": [
                "Manual review of submitted documentation."
            ],
            "reasoning": (
                "The validation agent could not complete "
                "its analysis. Human review is required."
            ),
            "human_review_required": True,
            "confidence": 0.0,
            "agent_error": str(exc),
        }

    # --------------------------------------------------------
    # 10. CRITIC AGENT
    #
    # The critic checks the output of the primary validation
    # agent before the final human-review decision.
    # --------------------------------------------------------

    critic_result = _call_critic_agent(
        features=features,
        validation_result=validation_result,
        document_text=document_text,
    )

    validation_result["critic_agent"] = critic_result

    # --------------------------------------------------------
    # 10b. Add severity / priority
    # --------------------------------------------------------

    validation_result = (
        _apply_human_review_priority(
            features,
            validation_result,
        )
    )

    # --------------------------------------------------------
    # 11. Human-review decision
    #
    # Existing agent decision OR missing documentation /
    # inconsistency OR clinically high severity.
    # --------------------------------------------------------

    severity_score = _safe_float(
        validation_result.get(
            "severity_score"
        ),
        0.0,
    )

    agent_requested_review = bool(
        validation_result.get(
            "human_review_required",
            False,
        )
    )

    missing_context = validation_result.get(
        "missing_context"
    ) or []

    inconsistencies = validation_result.get(
        "inconsistencies"
    ) or []

    documentation_needed = validation_result.get(
        "documentation_needed"
    ) or []

    critic_failed = (
        validation_result
        .get("critic_agent", {})
        .get("agent_working")
        is False
    )

    human_review_required = bool(
        agent_requested_review
        or missing_context
        or inconsistencies
        or documentation_needed
        or critic_failed
    )

    # --------------------------------------------------------
    # Important:
    #
    # If severity is CRITICAL/HIGH and the agent has already
    # identified the case as requiring human review, keep it
    # in the human queue.
    #
    # --------------------------------------------------------

    if severity_score >= 0.70:
        human_review_required = True

    validation_result[
        "human_review_required"
    ] = human_review_required

    req.features = {
        **(
            req.features
            or {}
        ),
        "validation_agent": validation_result,
    }

    db.flush()

    # --------------------------------------------------------
    # 12. Audit validation
    # --------------------------------------------------------

    log(
        db,
        "VALIDATION_AGENT_COMPLETED",
        request_id=req.id,
        actor=user,
        detail=validation_result,
    )

    # --------------------------------------------------------
    # 13. Existing adjudication engine
    # --------------------------------------------------------

    try:
        adjudicate(
            db,
            req,
            user,
        )

    except ml.ModelUnavailable as exc:
        db.rollback()

        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            str(exc),
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            (
                "Authorization adjudication failed: "
                f"{exc}"
            ),
        )

    # --------------------------------------------------------
    # 14. HUMAN REVIEW OVERRIDE
    # --------------------------------------------------------

    if human_review_required:

        priority_score = _safe_float(
            validation_result.get(
                "severity_score"
            ),
            0.30,
        )

        priority_level = (
            validation_result.get(
                "review_priority"
            )
            or validation_result.get(
                "clinical_severity"
            )
            or "LOW"
        )

        # ----------------------------------------------------
        # Force PENDING_REVIEW
        # ----------------------------------------------------

        req.status = "PENDING_REVIEW"

        req.decision = None
        req.decision_source = None
        req.decision_at = None

        # ----------------------------------------------------
        # Store priority score in urgency_score.
        #
        # Review queue can therefore sort:
        #
        # CRITICAL -> HIGH -> MEDIUM -> LOW
        # ----------------------------------------------------

        req.urgency_score = priority_score

        # ----------------------------------------------------
        # Store priority metadata inside features as well.
        # ----------------------------------------------------

        req.features = {
            **(
                req.features
                or {}
            ),
            "human_review": {
                "required": True,
                "priority": priority_level,
                "severity_score": priority_score,
                "sla": validation_result.get(
                    "sla"
                ),
            },
        }

        # ----------------------------------------------------
        # Try reviewer assignment.
        #
        # If no reviewer is available, DO NOT fail the request.
        # Keep it unassigned in the queue.
        # ----------------------------------------------------

        routing_result = {}

        try:
            routing_result = routing.assign(
                db,
                features,
            ) or {}

        except Exception as exc:
            print(
                "[REVIEW ROUTING WARNING]",
                exc,
            )

            routing_result = {
                "reviewer_id": None,
                "reason": (
                    "No reviewer could be assigned automatically."
                ),
                "reassigned": False,
                "candidates": [],
            }

        req.assigned_reviewer_id = (
            routing_result.get(
                "reviewer_id"
            )
        )

        req.assignment_reason = (
            routing_result.get(
                "reason"
            )
            or (
                "Assigned according to "
                f"{priority_level} clinical priority."
            )
        )

        req.assignment_was_reassigned = bool(
            routing_result.get(
                "reassigned",
                False,
            )
        )

        # ----------------------------------------------------
        # Queue audit
        # ----------------------------------------------------

        log(
            db,
            "HUMAN_REVIEW_QUEUED",
            request_id=req.id,
            actor=user,
            detail={
                "priority": priority_level,
                "severity_score": priority_score,
                "human_review_required": True,
                "assigned_reviewer_id": (
                    req.assigned_reviewer_id
                ),
                "assignment_reason": (
                    req.assignment_reason
                ),
                "routing_candidates": (
                    routing_result.get(
                        "candidates",
                        [],
                    )
                ),
            },
        )

        # ----------------------------------------------------
        # Reviewer assignment audit
        # ----------------------------------------------------

        if req.assigned_reviewer_id:

            log(
                db,
                "REVIEWER_ASSIGNED",
                request_id=req.id,
                actor=user,
                detail={
                    "reviewer_id": (
                        req.assigned_reviewer_id
                    ),
                    "reason": (
                        req.assignment_reason
                    ),
                    "priority": priority_level,
                    "severity_score": (
                        priority_score
                    ),
                },
            )

    # --------------------------------------------------------
    # 15. Commit
    # --------------------------------------------------------

    db.commit()
    db.refresh(req)

    # --------------------------------------------------------
    # 16. Return complete request
    # --------------------------------------------------------

    return _detail(
        db,
        req,
    )


# ============================================================
# LIST REQUESTS
# ============================================================

@router.get(
    "/requests"
)
def list_requests(
    user: User = Depends(
        require_provider
    ),
    db: Session = Depends(
        get_db
    ),
    status_filter: str | None = None,
):
    q = (
        db.query(AuthRequest)
        .filter(
            AuthRequest.organization_id
            == user.organization_id
        )
    )

    if status_filter:
        q = q.filter(
            AuthRequest.status
            == status_filter
        )

    rows = (
        q.order_by(
            desc(
                AuthRequest.created_at
            )
        )
        .limit(300)
        .all()
    )

    return [
        _summary(r)
        for r in rows
    ]


# ============================================================
# GET SINGLE REQUEST
# ============================================================

@router.get(
    "/requests/{request_id}"
)
def get_request(
    request_id: str,
    user: User = Depends(
        current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    req = db.get(
        AuthRequest,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No such case",
        )

    # Provider can only see cases belonging
    # to their organization.
    if (
        user.role == "PROVIDER_STAFF"
        and req.organization_id
        != user.organization_id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This case belongs to another organization",
        )

    return _detail(
        db,
        req,
    )


# ============================================================
# FILE APPEAL
# ============================================================

@router.post(
    "/requests/{request_id}/appeal",
    status_code=201,
)
def file_appeal(
    request_id: str,
    body: AppealCreate,
    user: User = Depends(
        require_provider
    ),
    db: Session = Depends(
        get_db
    ),
):
    req = db.get(
        AuthRequest,
        request_id,
    )

    if (
        req is None
        or req.organization_id
        != user.organization_id
    ):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No such case",
        )

    if req.decision != "DENIED":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Only denied cases can be appealed",
        )

    existing = (
        db.query(Appeal)
        .filter(
            Appeal.request_id
            == req.id,
            Appeal.status
            == "OPEN",
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An appeal is already open on this case",
        )

    appeal = Appeal(
        request_id=req.id,
        filed_by=user.id,
        rationale=body.rationale,
        new_documentation=body.new_documentation,
        predicted_at_filing=req.appeal_prediction,
    )

    db.add(appeal)

    req.status = "APPEALED"

    log(
        db,
        "APPEAL_FILED",
        request_id=req.id,
        actor=user,
        detail={
            "new_documentation": (
                body.new_documentation
            ),
            "model_predicted": (
                req.appeal_prediction
                or {}
            ).get(
                "top_class"
            ),
            "model_any_appeal_probability": (
                req.appeal_prediction
                or {}
            ).get(
                "any_appeal_probability"
            ),
        },
    )

    db.commit()
    db.refresh(appeal)

    return {
        "appeal_id": appeal.id,
        "status": appeal.status,
        "request_status": req.status,
    }


# ============================================================
# AUDIT TRAIL
# ============================================================

@router.get(
    "/requests/{request_id}/audit"
)
def audit_trail(
    request_id: str,
    user: User = Depends(
        current_user
    ),
    db: Session = Depends(
        get_db
    ),
):
    req = db.get(
        AuthRequest,
        request_id,
    )

    if req is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No such case",
        )

    if (
        user.role == "PROVIDER_STAFF"
        and req.organization_id
        != user.organization_id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This case belongs to another organization",
        )

    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.request_id
            == request_id
        )
        .order_by(
            AuditEvent.created_at
        )
        .all()
    )

    return [
        {
            "id": event.id,
            "action": event.action,
            "actor_email": event.actor_email,
            "detail": event.detail,
            "created_at": event.created_at,
        }
        for event in events
    ]


# ============================================================
# SUMMARY
# ============================================================

def _summary(
    r: AuthRequest,
) -> dict:

    features = r.features or {}

    validation = (
        features.get(
            "validation_agent"
        )
        or {}
    )

    human_review = (
        features.get(
            "human_review"
        )
        or {}
    )

    return {
        "id": r.id,
        "case_number": r.case_number,
        "status": r.status,
        "decision": r.decision,
        "decision_source": r.decision_source,
        "created_at": r.created_at,

        "policy_fit_score": (
            r.policy_fit_score
        ),
        "necessity_score": (
            r.necessity_score
        ),
        "urgency_score": (
            r.urgency_score
        ),
        "confidence": (
            r.confidence
        ),
        "processing_ms": (
            r.processing_ms
        ),

        "assigned_reviewer_id": (
            r.assigned_reviewer_id
        ),

        "assignment_reason": (
            r.assignment_reason
        ),

        "assignment_was_reassigned": (
            r.assignment_was_reassigned
        ),

        "diagnosis": features.get(
            "diagnosis"
        ),

        "requested_treatment": features.get(
            "requested_treatment"
        ),

        "disease_severity": features.get(
            "disease_severity"
        ),

        "provider_specialty": features.get(
            "provider_specialty"
        ),

        "payer": features.get(
            "payer"
        ),

        "appeal_probability": (
            r.appeal_prediction
            or {}
        ).get(
            "any_appeal_probability"
        ),

        # ----------------------------------------------------
        # Validation agent
        # ----------------------------------------------------

        "validation_agent": validation,

        "agent_validation": validation,

        # ----------------------------------------------------
        # Human review
        # ----------------------------------------------------

        "human_review_required": bool(
            validation.get(
                "human_review_required",
                False,
            )
        ),

        "severity_score": (
            validation.get(
                "severity_score"
            )
        ),

        "clinical_severity": (
            validation.get(
                "clinical_severity"
            )
        ),

        "review_priority": (
            validation.get(
                "review_priority"
            )
        ),

        "priority_label": (
            validation.get(
                "priority_label"
            )
        ),

        "review_sla": (
            validation.get(
                "sla"
            )
            or human_review.get(
                "sla"
            )
        ),
    }


# ============================================================
# RUN VALIDATION AGENT
# ============================================================

def _run_agent_for_request(
    db: Session,
    r: AuthRequest,
) -> dict:
    """
    Run validation once and persist the result.
    """

    features = dict(
        r.features or {}
    )

    stored = features.get(
        "validation_agent"
    )

    # --------------------------------------------------------
    # Existing validation
    # --------------------------------------------------------

    if isinstance(stored, dict):

        # ----------------------------------------------------
        # Existing validation result
        # ----------------------------------------------------

        enriched = dict(stored)

        # ----------------------------------------------------
        # Run critic if this request does not already have
        # a critic result.
        # ----------------------------------------------------

        if not isinstance(
            enriched.get("critic_agent"),
            dict,
        ):

            critic_result = _call_critic_agent(
                features=features,
                validation_result=enriched,
                document_text="",
            )

            enriched[
                "critic_agent"
            ] = critic_result

            # ------------------------------------------------
            # If the critic cannot verify the primary agent,
            # force human review.
            # ------------------------------------------------

            if (
                critic_result.get(
                    "agent_working"
                )
                is False
            ):

                enriched[
                    "human_review_required"
                ] = True

        enriched = (
            _apply_human_review_priority(
                features,
                enriched,
            )
        )

        r.features = {
            **features,
            "validation_agent": enriched,
        }

        db.flush()

        return enriched

    # --------------------------------------------------------
    # Documents
    # --------------------------------------------------------

    docs = (
        db.query(Document)
        .filter(
            Document.request_id
            == r.id
        )
        .all()
    )

    document_text = "\n\n".join(
        doc.raw_text
        for doc in docs
        if doc.raw_text
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    try:

        result = (
            _call_validation_agent(
                features=features,
                document_text=document_text,
            )
        )

    except Exception as exc:

        print(
            f"[VALIDATION AGENT ERROR] "
            f"Request {r.id}: {exc}"
        )

        result = {
            "contextually_complete": False,
            "consistency_check": "ERROR",
            "missing_context": [],
            "inconsistencies": [
                "Validation agent could not complete its analysis."
            ],
            "documentation_needed": [
                "Manual review of the submitted clinical documentation."
            ],
            "reasoning": (
                "The validation agent was unavailable. "
                "Human review is recommended."
            ),
            "human_review_required": True,
            "confidence": 0.0,
            "agent_error": str(exc),
        }

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    result = (
        _apply_human_review_priority(
            features,
            result,
        )
    )

    # --------------------------------------------------------
    # Human review
    # --------------------------------------------------------

    result[
        "human_review_required"
    ] = bool(
        result.get(
            "human_review_required",
            False,
        )
        or result.get(
            "severity_score",
            0,
        ) >= 0.70
        or result.get(
            "missing_context"
        )
        or result.get(
            "inconsistencies"
        )
        or result.get(
            "documentation_needed"
        )
    )

    # --------------------------------------------------------
    # Persist
    # --------------------------------------------------------

    r.features = {
        **features,
        "validation_agent": result,
    }

    db.flush()

    return result


# ============================================================
# COMPLETE REQUEST DETAIL
# ============================================================

def _detail(
    db: Session,
    r: AuthRequest,
) -> dict:

    # --------------------------------------------------------
    # Reviewer
    # --------------------------------------------------------

    reviewer = (
        db.get(
            User,
            r.assigned_reviewer_id,
        )
        if r.assigned_reviewer_id
        else None
    )

    # --------------------------------------------------------
    # Appeals
    # --------------------------------------------------------

    appeals = (
        db.query(Appeal)
        .filter(
            Appeal.request_id
            == r.id
        )
        .all()
    )

    # --------------------------------------------------------
    # Documents
    # --------------------------------------------------------

    docs = (
        db.query(Document)
        .filter(
            Document.request_id
            == r.id
        )
        .all()
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    agent_validation = (
        _run_agent_for_request(
            db,
            r,
        )
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    out = _summary(r)

    # --------------------------------------------------------
    # Detailed information
    # --------------------------------------------------------

    out.update(
        {
            "features": r.features,

            "criteria": r.criteria,

            "explanation": (
                r.explanation
            ),

            "appeal_prediction": (
                r.appeal_prediction
            ),

            "reviewer_notes": (
                r.reviewer_notes
            ),

            "documentation_score": (
                r.documentation_score
            ),

            "agent_validation": (
                agent_validation
            ),

            "assigned_reviewer": (
                {
                    "id": reviewer.id,
                    "name": reviewer.full_name,
                    "specialty": reviewer.specialty,
                }
                if reviewer
                else None
            ),

            "documents": [
                {
                    "id": document.id,
                    "filename": document.filename,
                    "page_count": document.page_count,
                    "extraction_confidence": (
                        document.extraction_confidence
                    ),
                }
                for document in docs
            ],

            "appeals": [
                {
                    "id": appeal.id,
                    "status": appeal.status,
                    "rationale": appeal.rationale,
                    "new_documentation": (
                        appeal.new_documentation
                    ),
                    "outcome_notes": (
                        appeal.outcome_notes
                    ),
                    "created_at": (
                        appeal.created_at
                    ),
                }
                for appeal in appeals
            ],
        }
    )

    return out