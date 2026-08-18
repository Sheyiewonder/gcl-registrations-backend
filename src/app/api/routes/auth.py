from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_db
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    hash_invitation_token,
)
from app.models.admin import Admin
from app.models.admin_otp import AdminOTP
from app.models.admin_invitation import AdminInvitation
from app.schemas.auth import PasswordSetupRequest
from app.schemas.auth import (
    AdminResponse,
    TokenResponse,
    VerifyOTPRequest,
    PasswordSetupRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

from app.models.admin_password_reset import AdminPasswordReset

from app.services.email import (
    send_admin_otp_email,
    send_admin_password_reset_email,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_REQUESTS = 10
OTP_REQUEST_WINDOW_MINUTES = 5

PASSWORD_RESET_EXPIRY_MINUTES = 30

def generate_otp() -> str:
    """Generate a secure 6-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Step 1:
    Verify admin email/password and send an OTP.
    """

    admin = (
        db.query(Admin)
        .filter(Admin.email == form_data.username)
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    if not verify_password(
        form_data.password,
        admin.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    now = datetime.utcnow()

    # ---------------------------------------------------------
    # Check recent OTP requests
    # ---------------------------------------------------------

    request_window = now - timedelta(
        minutes=OTP_REQUEST_WINDOW_MINUTES
    )

    recent_otp_count = (
        db.query(AdminOTP)
        .filter(
            AdminOTP.admin_id == admin.id,
            AdminOTP.created_at >= request_window,
        )
        .count()
    )

    if recent_otp_count >= OTP_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many OTP requests. "
                "Please wait before requesting another OTP."
            ),
        )

    # ---------------------------------------------------------
    # Check resend cooldown
    # ---------------------------------------------------------

   latest_otp = (
        db.query(AdminOTP)
        .filter(
            AdminOTP.admin_id == admin.id,
            AdminOTP.used_at.is_(None),
        )
        .order_by(AdminOTP.created_at.desc())
        .first()
    )

    if latest_otp:
        seconds_since_last_request = (
            now - latest_otp.created_at
        ).total_seconds()

        if seconds_since_last_request < OTP_RESEND_COOLDOWN_SECONDS:
            remaining = int(
                OTP_RESEND_COOLDOWN_SECONDS
                - seconds_since_last_request
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Please wait {remaining} seconds "
                    "before requesting another OTP."
                ),
            )
    # ---------------------------------------------------------
    # Invalidate previous unused OTPs
    # ---------------------------------------------------------

    active_otps = (
        db.query(AdminOTP)
        .filter(
            AdminOTP.admin_id == admin.id,
            AdminOTP.used_at.is_(None),
        )
        .all()
    )

    for otp in active_otps:
        otp.used_at = now

    # ---------------------------------------------------------
    # Generate new OTP
    # ---------------------------------------------------------

    otp = generate_otp()

    otp_record = AdminOTP(
        admin_id=admin.id,
        otp_hash=hash_password(otp),
        expires_at=now + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        ),
        attempts=0,
    )

    db.add(otp_record)
    db.commit()

    # ---------------------------------------------------------
    # DEVELOPMENT ONLY
    # ---------------------------------------------------------
    # Replace this with your email service later.
    await send_admin_otp_email(
        email=admin.email,
        otp=otp,
        expires_minutes=OTP_EXPIRY_MINUTES,
    )

    return {
        "message": "OTP sent successfully",
        "email": admin.email,
        "requires_otp": True,
    }


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
)
def verify_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    """
    Step 2:
    Verify the OTP and issue the JWT access token.
    """

    admin = (
        db.query(Admin)
        .filter(Admin.email == data.email)
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    otp_record = (
        db.query(AdminOTP)
        .filter(
            AdminOTP.admin_id == admin.id,
            AdminOTP.used_at.is_(None),
        )
        .order_by(AdminOTP.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active OTP found",
        )

    now = datetime.utcnow()

    # ---------------------------------------------------------
    # Check expiry
    # ---------------------------------------------------------

    if now >= otp_record.expires_at:
        otp_record.used_at = now
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP has expired",
        )

    # ---------------------------------------------------------
    # Check attempt limit
    # ---------------------------------------------------------

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.used_at = now
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many incorrect OTP attempts. "
                "Please request a new OTP."
            ),
        )

    # ---------------------------------------------------------
    # Verify OTP
    # ---------------------------------------------------------

    if not verify_password(
        data.otp,
        otp_record.otp_hash,
    ):
        otp_record.attempts += 1
        db.commit()

        remaining = OTP_MAX_ATTEMPTS - otp_record.attempts

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid OTP. "
                f"{remaining} attempt(s) remaining."
            ),
        )

    # ---------------------------------------------------------
    # OTP is valid
    # ---------------------------------------------------------

    otp_record.used_at = now

    db.commit()

    access_token = create_access_token(
        subject=str(admin.id),
        role=admin.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/setup-password")
def setup_password(
    data: PasswordSetupRequest,
    db: Session = Depends(get_db),
):
    invitation = (
        db.query(AdminInvitation)
        .filter(
            AdminInvitation.token_hash
            == hash_invitation_token(data.token),
            AdminInvitation.used_at.is_(None),
        )
        .first()
    )

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used invitation",
        )

    now = datetime.utcnow()

    if now >= invitation.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    admin = db.get(Admin, invitation.admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin account not found",
        )

    admin.hashed_password = hash_password(
        data.password
    )

    invitation.used_at = now

    admin.is_active = True


    db.commit()

    return {
        "message": "Password set successfully. You can now log in."
    }

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset email.

    Always returns the same response whether or not
    the email exists, preventing account enumeration.
    """

    admin = (
        db.query(Admin)
        .filter(Admin.email == data.email)
        .first()
    )

    # Do not reveal whether the account exists.
    if not admin:
        return {
            "message": (
                "If an administrator account exists "
                "for this email, a password reset link "
                "has been sent."
            )
        }

    now = datetime.utcnow()

    # Invalidate previous unused reset tokens.
    active_resets = (
        db.query(AdminPasswordReset)
        .filter(
            AdminPasswordReset.admin_id == admin.id,
            AdminPasswordReset.used_at.is_(None),
        )
        .all()
    )

    for reset in active_resets:
        reset.used_at = now

    reset_token = secrets.token_urlsafe(48)

    reset_record = AdminPasswordReset(
        admin_id=admin.id,
        token_hash=hash_invitation_token(reset_token),
        expires_at=(
            now
            + timedelta(
                minutes=PASSWORD_RESET_EXPIRY_MINUTES
            )
        ),
    )

    db.add(reset_record)
    db.commit()

    await send_admin_password_reset_email(
        email=admin.email,
        reset_token=reset_token,
        expires_minutes=PASSWORD_RESET_EXPIRY_MINUTES,
    )

    return {
        "message": (
            "If an administrator account exists "
            "for this email, a password reset link "
            "has been sent."
        )
    }

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_record = (
        db.query(AdminPasswordReset)
        .filter(
            AdminPasswordReset.token_hash
            == hash_invitation_token(data.token),
            AdminPasswordReset.used_at.is_(None),
        )
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used password reset link",
        )

    now = datetime.utcnow()

    if now >= reset_record.expires_at:
        reset_record.used_at = now
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link has expired",
        )

    admin = db.get(
        Admin,
        reset_record.admin_id,
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator account not found",
        )

    admin.hashed_password = hash_password(
        data.password
    )

    reset_record.used_at = now

    db.commit()

    return {
        "message": (
            "Password reset successfully. "
            "You can now log in."
        )
    }


@router.get(
    "/me",
    response_model=AdminResponse,
)
def get_me(
    current_admin: Admin = Depends(get_current_admin),
):
    return current_admin