from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_super_admin
from app.core.security import (
    generate_invitation_token,
    hash_invitation_token,
    hash_password,
)
from app.models.admin import Admin
from app.models.admin_invitation import AdminInvitation
from app.schemas.admin import (
    AdminCreate,
    AdminResponse,
    AdminRoleUpdate,
    AdminStatusUpdate,
)
from app.services.email import send_admin_invitation_email


router = APIRouter(
    prefix="/admins",
    tags=["Admin Management"],
)


INVITATION_EXPIRY_HOURS = 24


def get_admin_status(
    admin: Admin,
    db: Session,
) -> str:
    """
    Determine the current status of an admin.

    Pending:
        The admin has an unused invitation.

    Active:
        The invitation has been completed and the account is active.

    Inactive:
        The invitation has been completed and the account is inactive.
    """

    invitation = (
        db.query(AdminInvitation)
        .filter(
            AdminInvitation.admin_id == admin.id,
            AdminInvitation.used_at.is_(None),
        )
        .order_by(AdminInvitation.created_at.desc())
        .first()
    )

    if invitation:
        return "pending"

    if admin.is_active:
        return "active"

    return "inactive"


def build_admin_response(
    admin: Admin,
    db: Session,
) -> AdminResponse:
    """
    Build the API response including the computed admin status.
    """

    return AdminResponse(
        id=admin.id,
        email=admin.email,
        role=admin.role,
        is_active=admin.is_active,
        status=get_admin_status(admin, db),
        created_at=admin.created_at,
    )


@router.post(
    "",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin(
    data: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    existing_admin = (
        db.query(Admin)
        .filter(Admin.email == data.email)
        .first()
    )

    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin with this email already exists",
        )

    if data.role not in {"admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin role",
        )

    # Temporary password.
    # The invited admin cannot use this password because
    # they must complete password setup through the invitation.
    temporary_password = secrets.token_urlsafe(32)

    new_admin = Admin(
        email=data.email,
        hashed_password=hash_password(temporary_password),
        role=data.role,
        is_active=False,
    )

    db.add(new_admin)
    db.flush()

    # Generate invitation token.
    invitation_token = generate_invitation_token()

    invitation = AdminInvitation(
        admin_id=new_admin.id,
        token_hash=hash_invitation_token(
            invitation_token
        ),
        expires_at=(
            datetime.utcnow()
            + timedelta(hours=INVITATION_EXPIRY_HOURS)
        ),
    )

    db.add(invitation)

    db.commit()
    db.refresh(new_admin)

    # Send invitation email.
    await send_admin_invitation_email(
        email=new_admin.email,
        invitation_token=invitation_token,
        expires_hours=INVITATION_EXPIRY_HOURS,
    )

    return build_admin_response(
        new_admin,
        db,
    )


@router.get(
    "",
    response_model=list[AdminResponse],
)
def get_admins(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    admins = (
        db.query(Admin)
        .order_by(Admin.created_at.desc())
        .all()
    )

    return [
        build_admin_response(admin, db)
        for admin in admins
    ]


@router.get(
    "/{admin_id}",
    response_model=AdminResponse,
)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    admin = db.get(Admin, admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    return build_admin_response(
        admin,
        db,
    )


@router.patch(
    "/{admin_id}/status",
    response_model=AdminResponse,
)
def update_admin_status(
    admin_id: int,
    data: AdminStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    admin = db.get(Admin, admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    # ---------------------------------------------------------
    # Pending admins cannot be activated or deactivated.
    # They must complete password setup first.
    # ---------------------------------------------------------

    invitation = (
        db.query(AdminInvitation)
        .filter(
            AdminInvitation.admin_id == admin.id,
            AdminInvitation.used_at.is_(None),
        )
        .order_by(AdminInvitation.created_at.desc())
        .first()
    )

    if invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This admin is still pending. "
                "They must set up their password before "
                "their account status can be changed."
            ),
        )

    # ---------------------------------------------------------
    # Prevent super admin from deactivating themselves.
    # ---------------------------------------------------------

    if admin.id == current_admin.id and not data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate yourself",
        )

    admin.is_active = data.is_active

    db.commit()
    db.refresh(admin)

    return build_admin_response(
        admin,
        db,
    )


@router.patch(
    "/{admin_id}/role",
    response_model=AdminResponse,
)
def update_admin_role(
    admin_id: int,
    data: AdminRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    admin = db.get(Admin, admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    if data.role not in {"admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin role",
        )

    if admin.id == current_admin.id and data.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own super admin role",
        )

    admin.role = data.role

    db.commit()
    db.refresh(admin)

    return build_admin_response(
        admin,
        db,
    )


@router.delete(
    "/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    admin = db.get(Admin, admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    if admin.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself",
        )

    db.delete(admin)
    db.commit()

    return None