"""Authentication routes - giữ nguyên từ main.py"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from ..database import get_db, hash_password
from ..auth import verify_password, create_access_token, get_current_user
from ..models import UserCreate, User, Token

router = APIRouter()

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            logger.warning(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user["password_hash"]):
            logger.warning(f"Invalid password for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Creating access token for user: {user['username']}")
        access_token = create_access_token(user["id"])
        logger.info(f"User {user['username']} logged in successfully")
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """Register a new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Không cho phép đăng ký username "admin"
    if user.username.lower() == "admin":
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể đăng ký với username 'admin'. Tài khoản admin đã được tạo sẵn."
        )
    
    # Check if username or email already exists
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                   (user.username, user.email))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username hoặc email đã được đăng ký"
        )
    
    # Create new user (always as regular user, not admin)
    user_id = str(uuid.uuid4())
    password_hash = hash_password(user.password)
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO users (id, username, email, password_hash, full_name, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, user.username, user.email, password_hash, user.full_name, 0, created_at))
    
    conn.commit()
    conn.close()
    
    logger.info(f"New user registered: {user.username}")
    
    return User(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_admin=False,
        created_at=created_at
    )

@router.get("/users/me", response_model=User)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return User(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        is_admin=bool(current_user["is_admin"]),
        created_at=current_user["created_at"]
    )
