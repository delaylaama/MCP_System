"""Security, Password Hashing, and JWT utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
import hmac
import hashlib
import secrets
from backend.app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate secure password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_oauth_state(user_id: str) -> str:
    """Generate cryptographically secure state parameter bound to user_id to prevent CSRF."""
    random_part = secrets.token_urlsafe(24)
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        f"{user_id}:{random_part}".encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{user_id}:{random_part}:{signature}"


def verify_oauth_state(state: str) -> Optional[str]:
    """Validate OAuth state parameter and return user_id if valid."""
    try:
        parts = state.split(":")
        if len(parts) != 3:
            return None
        user_id, random_part, signature = parts
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            f"{user_id}:{random_part}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        if hmac.compare_digest(signature, expected_sig):
            return user_id
        return None
    except Exception:
        return None
