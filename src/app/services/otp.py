import secrets
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password


OTP_EXPIRE_MINUTES = 10


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    return hash_password(otp)


def otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        minutes=OTP_EXPIRE_MINUTES
    )