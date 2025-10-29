"""Auth helpers - giữ nguyên từ main.py"""
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from .database import get_db
from .config import active_tokens

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return hash_password(plain_password) == hashed_password

def create_access_token(user_id: str) -> str:
    """Create simple access token"""
    # Generate random token
    token = str(uuid.uuid4()) + str(uuid.uuid4()).replace("-", "")
    # Set expiration (24 hours)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    # Store in memory
    active_tokens[token] = {
        "user_id": user_id,
        "expires_at": expires_at
    }
    return token

def verify_token(token: str) -> Optional[str]:
    """Verify token and return user_id if valid"""
    if token not in active_tokens:
        return None
    
    token_data = active_tokens[token]
    # Check if expired
    if datetime.utcnow() > token_data["expires_at"]:
        del active_tokens[token]
        return None
    
    return token_data["user_id"]

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id = verify_token(token)
    if not user_id:
        raise credentials_exception
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    
    return dict(user)
