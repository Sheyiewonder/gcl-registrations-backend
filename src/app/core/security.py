from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings

import secrets
import hashlib

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_otp(otp: str) -> str:
    return password_hash.hash(otp)

def verify_otp(otp: str, hashed_otp: str) -> bool:
    return password_hash.verify(otp, hashed_otp)

def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)

def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

def create_access_token(
    subject: str,
    role: str,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )