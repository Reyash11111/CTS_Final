from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditEvent, AuthRequest, Document, Organization, User
from ..security import current_user


router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================
# ADMIN ACCESS
# ============================================================

def require_admin(user: User = Depends(current_user)) -> User:
    if user.role not in {"PROVIDER_ADMIN", "PAYER_ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return user


# ============================================================
# HELPERS
# ============================================================

def iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def user_summary(user: User):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "specialty": user.specialty,
        "license_number": user.license_number,
        "daily_capacity": user.daily_capacity,
        "is_available": user.is_available,
        "unavailable_reason": user.unavailable_reason,
        "created_at": iso(user.created_at),
        "last_login_at": iso(user.last_login_at),
    }


def request_summary(request: AuthRequest, creator: User | None = None, documents=None):
    features = request.features or {}
    documents = documents or []

    return {
        "id": request.id,
        "case_number": request.case_number,
        "status": request.status,
        "decision": request.decision,
        "decision_source": request.decision_source,
        "created_at": iso(request.created_at),
        "decision_at": iso(request.decision_at),
        "diagnosis": features.get("diagnosis"),
        "requested_treatment": features.get("requested_treatment"),
        "disease_severity": features.get("disease_severity"),
        "provider_specialty": features.get("provider_specialty"),
        "payer": features.get("payer"),
        "policy_fit_score": request.policy_fit_score,
        "documentation_score": request.documentation_score,
        "necessity_score": request.necessity_score,
        "urgency_score": request.urgency_score,
        "confidence": request.confidence,
        "created_by": (
            {
                "id": creator.id,
                "name": creator.full_name,
                "email": creator.email,
            }
            if creator
            else None
        ),
        "assigned_reviewer_id": request.assigned_reviewer_id,
        "assignment_reason": request.assignment_reason,
        "assignment_was_reassigned": request.assignment_was_reassigned,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "page_count": d.page_count,
                "char_count": d.char_count,
                "extraction_confidence": d.extraction_confidence,
                "created_at": iso(d.created_at),
                "uploaded_by": d.uploaded_by,
            }
            for d in documents
        ],
    }


def audit_summary(event: AuditEvent):
    return {
        "id": event.id,
        "request_id": event.request_id,
        "actor_id": event.actor_id,
        "actor_email": event.actor_email,
        "action": event.action,
        "detail": event.detail or {},
        "created_at": iso(event.created_at),
    }


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("/dashboard")
def admin_dashboard(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return live organization-scoped admin information."""

    organization = db.get(Organization, user.organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    # --------------------------------------------------------
    # 1. STAFF BELONGING TO THIS ORGANIZATION
    # --------------------------------------------------------
    staff_role = (
        "PROVIDER_STAFF"
        if user.role == "PROVIDER_ADMIN"
        else "PAYER_REVIEWER"
    )

    staff = (
        db.query(User)
        .filter(
            User.organization_id == user.organization_id,
            User.role == staff_role,
        )
        .order_by(User.created_at.desc())
        .all()
    )
    staff_ids = [s.id for s in staff]

    # --------------------------------------------------------
    # 2. CASES VISIBLE TO THIS ADMIN
    # --------------------------------------------------------
    if user.role == "PROVIDER_ADMIN":
        requests = (
            db.query(AuthRequest)
            .filter(AuthRequest.organization_id == user.organization_id)
            .order_by(AuthRequest.created_at.desc())
            .all()
        )
    else:
        # A payer admin sees cases assigned to its reviewers.
        assigned = []
        if staff_ids:
            assigned = (
                db.query(AuthRequest)
                .filter(AuthRequest.assigned_reviewer_id.in_(staff_ids))
                .order_by(AuthRequest.created_at.desc())
                .all()
            )

        # Also include cases whose extracted payer name matches this
        # insurance organization. This keeps the admin dashboard useful
        # even before reviewer assignment has happened.
        all_with_features = (
            db.query(AuthRequest)
            .filter(AuthRequest.features.isnot(None))
            .order_by(AuthRequest.created_at.desc())
            .all()
        )
        org_name = organization.name.strip().lower()
        payer_named = [
            r
            for r in all_with_features
            if str((r.features or {}).get("payer", "")).strip().lower()
            == org_name
        ]

        seen = set()
        requests = []
        for row in assigned + payer_named:
            if row.id not in seen:
                seen.add(row.id)
                requests.append(row)

    request_ids = [r.id for r in requests]

    # --------------------------------------------------------
    # 3. DOCUMENTS
    # --------------------------------------------------------
    # Hospital admin: documents uploaded by its staff OR attached to
    # hospital requests.
    # Payer admin: documents attached to payer-visible cases OR uploaded
    # by its reviewers.
    document_conditions = []
    if staff_ids:
        document_conditions.append(Document.uploaded_by.in_(staff_ids))
    if request_ids:
        document_conditions.append(Document.request_id.in_(request_ids))

    if document_conditions:
        documents = (
            db.query(Document)
            .filter(or_(*document_conditions))
            .order_by(Document.created_at.desc())
            .all()
        )
    else:
        documents = []

    documents_by_request = {}
    for document in documents:
        if document.request_id:
            documents_by_request.setdefault(document.request_id, []).append(document)

    # --------------------------------------------------------
    # 4. CREATOR CACHE
    # --------------------------------------------------------
    creator_ids = {r.created_by for r in requests if r.created_by}
    creators = {}
    if creator_ids:
        creators = {
            u.id: u
            for u in db.query(User).filter(User.id.in_(creator_ids)).all()
        }

    case_rows = [
        request_summary(
            request,
            creator=creators.get(request.created_by),
            documents=documents_by_request.get(request.id, []),
        )
        for request in requests
    ]

    # --------------------------------------------------------
    # 5. ORGANIZATION-SCOPED AUDIT EVENTS
    # --------------------------------------------------------
    # Include the admin itself, organization staff, and events attached
    # to cases visible to this dashboard.
    audit_conditions = [AuditEvent.actor_id == user.id]
    if staff_ids:
        audit_conditions.append(AuditEvent.actor_id.in_(staff_ids))
    if request_ids:
        audit_conditions.append(AuditEvent.request_id.in_(request_ids))

    audit_events = (
        db.query(AuditEvent)
        .filter(or_(*audit_conditions))
        .order_by(AuditEvent.created_at.desc())
        .limit(500)
        .all()
    )

    audit_rows = [audit_summary(event) for event in audit_events]

    # --------------------------------------------------------
    # 6. DOCUMENT ACTIVITY
    # --------------------------------------------------------
    uploader_ids = {d.uploaded_by for d in documents if d.uploaded_by}
    uploaders = {}
    if uploader_ids:
        uploaders = {
            u.id: u
            for u in db.query(User).filter(User.id.in_(uploader_ids)).all()
        }

    document_activity = [
        {
            "id": d.id,
            "filename": d.filename,
            "request_id": d.request_id,
            "uploaded_by": d.uploaded_by,
            "uploaded_by_name": (
                uploaders[d.uploaded_by].full_name
                if d.uploaded_by in uploaders
                else None
            ),
            "uploaded_by_email": (
                uploaders[d.uploaded_by].email
                if d.uploaded_by in uploaders
                else None
            ),
            "page_count": d.page_count,
            "char_count": d.char_count,
            "extraction_confidence": d.extraction_confidence,
            "created_at": iso(d.created_at),
        }
        for d in documents
    ]

    # --------------------------------------------------------
    # 7. LOGIN HISTORY
    # --------------------------------------------------------
    # Only staff/reviewer logins are shown here. Admin logins remain in
    # the complete audit log below.
    staff_id_set = set(staff_ids)
    login_history = [
        event
        for event in audit_rows
        if event["action"] == "USER_LOGIN"
        and event["actor_id"] in staff_id_set
    ]

    # --------------------------------------------------------
    # 8. PER-STAFF HISTORY
    # --------------------------------------------------------
    # This is the data needed for the admin to answer:
    # "When did this person log in? What did they upload? What did they do?"
    uploads_by_staff = {}
    for d in documents:
        if d.uploaded_by:
            uploads_by_staff[d.uploaded_by] = uploads_by_staff.get(d.uploaded_by, 0) + 1

    cases_by_staff = {}
    for r in requests:
        if r.created_by:
            cases_by_staff[r.created_by] = cases_by_staff.get(r.created_by, 0) + 1

    events_by_staff = {}
    logins_by_staff = {}
    last_activity_by_staff = {}
    for event in audit_rows:
        actor_id = event.get("actor_id")
        if actor_id not in staff_id_set:
            continue
        events_by_staff[actor_id] = events_by_staff.get(actor_id, 0) + 1
        if event["action"] == "USER_LOGIN":
            logins_by_staff[actor_id] = logins_by_staff.get(actor_id, 0) + 1
        current = last_activity_by_staff.get(actor_id)
        if current is None or (event.get("created_at") or "") > current:
            last_activity_by_staff[actor_id] = event.get("created_at")

    staff_history = []
    for member in staff:
        staff_history.append(
            {
                **user_summary(member),
                "login_count": logins_by_staff.get(member.id, 0),
                "upload_count": uploads_by_staff.get(member.id, 0),
                "case_count": cases_by_staff.get(member.id, 0),
                "activity_count": events_by_staff.get(member.id, 0),
                "last_activity_at": last_activity_by_staff.get(member.id),
            }
        )

    # --------------------------------------------------------
    # 9. COUNTS
    # --------------------------------------------------------
    completed_statuses = {"APPROVED", "DENIED", "AUTO_APPROVED", "AUTO_DENIED"}
    approved_statuses = {"APPROVED", "AUTO_APPROVED"}
    denied_statuses = {"DENIED", "AUTO_DENIED"}

    total_cases = len(requests)
    completed_cases = sum(r.status in completed_statuses for r in requests)
    pending_cases = sum(r.status == "PENDING_REVIEW" for r in requests)
    approved_cases = sum(r.status in approved_statuses for r in requests)
    denied_cases = sum(r.status in denied_statuses for r in requests)
    active_staff = sum(s.last_login_at is not None for s in staff)

    return {
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "org_type": organization.org_type,
        },
        "admin": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "role": user.role,
        },
        "overview": {
            "total_staff": len(staff),
            "active_staff": active_staff,
            "total_cases": total_cases,
            "completed_cases": completed_cases,
            "pending_cases": pending_cases,
            "approved_cases": approved_cases,
            "denied_cases": denied_cases,
            "total_documents": len(documents),
            "total_audit_events": len(audit_events),
        },
        "staff": [user_summary(s) for s in staff],
        "staff_history": staff_history,
        "cases": case_rows,
        "documents": document_activity,
        "staff_activity": audit_rows,
        "login_history": login_history,
        "audit_logs": audit_rows,
        "organization_activity": audit_rows[:50],
    }
