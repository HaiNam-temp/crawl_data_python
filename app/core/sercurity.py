from datetime import datetime, timedelta
from typing import Optional
import os
import hashlib
import bcrypt

# Delay optional heavy imports (passlib, jwt) until functions are called so module can be
# imported in environments where dev dependencies are not installed.


def _get_pwd_ctx():
    try:
        from passlib.context import CryptContext
    except Exception as exc:  # pragma: no cover - environment dependent
        raise ImportError("passlib is required for password hashing. Install passlib[bcrypt]") from exc
    return CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_jwt_module():
    try:
        import jwt
    except Exception as exc:  # pragma: no cover - environment dependent
        raise ImportError("PyJWT is required for JWT creation. Install PyJWT") from exc
    return jwt


JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_SECRET")  # override with env in production
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", 60 * 24))  # default 1 day


def hash_password(password: str) -> str:
    # băm SHA256 trước để tránh mật khẩu dài gây lỗi 72 bytes
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return bcrypt.hashpw(digest, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return bcrypt.checkpw(digest, hashed.encode("utf-8"))


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    jwt = _get_jwt_module()
    now = datetime.utcnow()
    if expires_delta is None:
        expires = now + timedelta(minutes=JWT_EXP_MINUTES)
    else:
        expires = now + expires_delta

    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Returns payload dict or raises an exception from PyJWT."""
    jwt = _get_jwt_module()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        # propagate exception to caller (HTTP layer will handle)
        raise