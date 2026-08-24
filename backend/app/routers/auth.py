from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organization, User

from ..schemas import (
    AvailabilityUpdate,
    Login,
    SignupAdmin,
    SignupPayer,
    SignupProvider,
    TokenOut,
    UserOut,
)

from ..security import (
    create_access_token,
    current_user,
    hash_password,
    require_payer,
    verify_password,
)

from ..services.pipeline import log
from ..services.vocab import SPECIALTIES


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


# =========================================================
# USER OUTPUT
# =========================================================

def _out(user: User) -> UserOut:

    data = UserOut.model_validate(user)

    data.organization_name = (
        user.organization.name
        if user.organization
        else None
    )

    return data


# =========================================================
# ORGANIZATION
# =========================================================

def _get_or_create_org(
    db: Session,
    name: str,
    org_type: str,
) -> Organization:

    normalized_name = name.strip()

    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Organization name is required.",
        )

    org = (
        db.query(Organization)
        .filter(
            func.lower(Organization.name) == normalized_name.lower(),
            Organization.org_type == org_type,
        )
        .first()
    )

    if org is None:

        org = Organization(
            name=name.strip(),
            org_type=org_type,
        )

        db.add(org)

        db.flush()

    return org


# =========================================================
# DUPLICATE EMAIL
# =========================================================

def _reject_duplicate(
    db: Session,
    email: str,
):

    existing = (
        db.query(User)
        .filter(
            User.email == email.lower()
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already uses this email address",
        )


# =========================================================
# SPECIALTIES
# =========================================================

@router.get("/specialties")
def specialties():

    return {
        "specialties": SPECIALTIES
    }


# =========================================================
# HOSPITAL STAFF SIGNUP
# =========================================================

@router.post(
    "/signup/provider",
    response_model=TokenOut,
    status_code=201,
)
def signup_provider(
    body: SignupProvider,
    db: Session = Depends(get_db),
):

    _reject_duplicate(
        db,
        body.email,
    )

    org = _get_or_create_org(
        db,
        body.organization_name,
        "PROVIDER",
    )

    user = User(

        email=body.email.lower(),

        password_hash=hash_password(
            body.password
        ),

        full_name=body.full_name.strip(),

        role="PROVIDER_STAFF",

        organization_id=org.id,

    )

    db.add(user)

    db.flush()

    log(
        db,
        "USER_REGISTERED",
        actor=user,
        detail={
            "portal": "provider",
            "role": "PROVIDER_STAFF",
            "organization": org.name,
        },
    )

    db.commit()

    db.refresh(user)

    return TokenOut(
        access_token=create_access_token(user),
        user=_out(user),
    )


# =========================================================
# INSURANCE STAFF SIGNUP
# =========================================================

@router.post(
    "/signup/payer",
    response_model=TokenOut,
    status_code=201,
)
def signup_payer(
    body: SignupPayer,
    db: Session = Depends(get_db),
):

    _reject_duplicate(
        db,
        body.email,
    )

    if body.specialty not in SPECIALTIES:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Choose a specialty from: "
                f"{', '.join(SPECIALTIES)}"
            ),
        )

    org = _get_or_create_org(
        db,
        body.organization_name,
        "PAYER",
    )

    user = User(

        email=body.email.lower(),

        password_hash=hash_password(
            body.password
        ),

        full_name=body.full_name.strip(),

        role="PAYER_REVIEWER",

        organization_id=org.id,

        specialty=body.specialty,

        license_number=body.license_number,

        daily_capacity=body.daily_capacity,

        is_available=True,

    )

    db.add(user)

    db.flush()

    log(
        db,
        "USER_REGISTERED",
        actor=user,
        detail={
            "portal": "payer",
            "role": "PAYER_REVIEWER",
            "specialty": body.specialty,
            "organization": org.name,
        },
    )

    db.commit()

    db.refresh(user)

    return TokenOut(
        access_token=create_access_token(user),
        user=_out(user),
    )


# =========================================================
# HOSPITAL ADMIN SIGNUP
# =========================================================

@router.post(
    "/signup/provider/admin",
    response_model=TokenOut,
    status_code=201,
)
def signup_provider_admin(
    body: SignupAdmin,
    db: Session = Depends(get_db),
):

    _reject_duplicate(
        db,
        body.email,
    )

    org = _get_or_create_org(
        db,
        body.organization_name,
        "PROVIDER",
    )

    user = User(

        email=body.email.lower(),

        password_hash=hash_password(
            body.password
        ),

        full_name=body.full_name.strip(),

        role="PROVIDER_ADMIN",

        organization_id=org.id,

    )

    db.add(user)

    db.flush()

    log(
        db,
        "ADMIN_REGISTERED",
        actor=user,
        detail={
            "portal": "provider",
            "role": "PROVIDER_ADMIN",
            "organization": org.name,
        },
    )

    db.commit()

    db.refresh(user)

    return TokenOut(
        access_token=create_access_token(user),
        user=_out(user),
    )


# =========================================================
# INSURANCE ADMIN SIGNUP
# =========================================================

@router.post(
    "/signup/payer/admin",
    response_model=TokenOut,
    status_code=201,
)
def signup_payer_admin(
    body: SignupAdmin,
    db: Session = Depends(get_db),
):

    _reject_duplicate(
        db,
        body.email,
    )

    org = _get_or_create_org(
        db,
        body.organization_name,
        "PAYER",
    )

    user = User(

        email=body.email.lower(),

        password_hash=hash_password(
            body.password
        ),

        full_name=body.full_name.strip(),

        role="PAYER_ADMIN",

        organization_id=org.id,

    )

    db.add(user)

    db.flush()

    log(
        db,
        "ADMIN_REGISTERED",
        actor=user,
        detail={
            "portal": "payer",
            "role": "PAYER_ADMIN",
            "organization": org.name,
        },
    )

    db.commit()

    db.refresh(user)

    return TokenOut(
        access_token=create_access_token(user),
        user=_out(user),
    )


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=TokenOut,
)
def login(
    body: Login,
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(
            User.email == body.email.lower()
        )
        .first()
    )

    if (
        user is None
        or not verify_password(
            body.password,
            user.password_hash,
        )
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect",
        )


    # =====================================================
    # HOSPITAL
    # =====================================================

    if body.portal == "provider":

        allowed_roles = {
            "PROVIDER_STAFF",
            "PROVIDER_ADMIN",
        }

        if user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This account belongs to the "
                    "insurance portal. "
                    "Switch portals to sign in."
                ),
            )


    # =====================================================
    # INSURANCE
    # =====================================================

    elif body.portal == "payer":

        allowed_roles = {
            "PAYER_REVIEWER",
            "PAYER_ADMIN",
        }

        if user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This account belongs to the "
                    "hospital portal. "
                    "Switch portals to sign in."
                ),
            )


    else:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid portal.",
        )


    # =====================================================
    # UPDATE LAST LOGIN
    # =====================================================

    user.last_login_at = datetime.now(
        timezone.utc
    )

    log(
        db,
        "USER_LOGIN",
        actor=user,
        detail={
            "portal": body.portal,
            "role": user.role,
        },
    )

    db.commit()

    db.refresh(user)


    return TokenOut(
        access_token=create_access_token(user),
        user=_out(user),
    )


# =========================================================
# CURRENT USER
# =========================================================

@router.get(
    "/me",
    response_model=UserOut,
)
def me(
    user: User = Depends(current_user),
):

    return _out(user)


# =========================================================
# REVIEWER AVAILABILITY
# =========================================================

@router.patch(
    "/availability",
    response_model=UserOut,
)
def set_availability(
    body: AvailabilityUpdate,
    user: User = Depends(require_payer),
    db: Session = Depends(get_db),
):

    user.is_available = body.is_available

    user.unavailable_reason = (
        None
        if body.is_available
        else (
            body.unavailable_reason
            or "Marked unavailable"
        )
    )

    log(
        db,
        "REVIEWER_AVAILABILITY_CHANGED",
        actor=user,
        detail={
            "is_available": body.is_available,
            "reason": user.unavailable_reason,
        },
    )

    db.commit()

    db.refresh(user)

    return _out(user)