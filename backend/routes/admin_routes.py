"""Admin routes - giữ nguyên từ main.py"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Platform, PlatformCreate

router = APIRouter()

@router.get("/admin/users/", response_model=List[User])
async def get_all_users(current_user: Dict = Depends(get_current_user)):
    """Get all users (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all users"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    return [
        User(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            is_admin=bool(user["is_admin"]),
            created_at=user["created_at"]
        )
        for user in users
    ]

@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a user (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )
    
    # Prevent deleting self
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Delete user's conversations and messages
    cursor.execute("SELECT id FROM conversations WHERE user_id = ?", (user_id,))
    conversations = cursor.fetchall()
    for conv in conversations:
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv["id"],))
    cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    
    # Delete user
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    conn.commit()
    conn.close()
    
    logger.info(f"User deleted: {user_id}")
    return None

@router.get("/admin/stats")
async def get_stats(current_user: Dict = Depends(get_current_user)):
    """Get system statistics (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view stats"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Count users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()["count"]
    
    # Count conversations
    cursor.execute("SELECT COUNT(*) as count FROM conversations")
    total_conversations = cursor.fetchone()["count"]
    
    # Count messages
    cursor.execute("SELECT COUNT(*) as count FROM messages")
    total_messages = cursor.fetchone()["count"]
    
    # Count platforms
    cursor.execute("SELECT COUNT(*) as count FROM platforms")
    total_platforms = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_platforms": total_platforms
    }

@router.get("/platforms/", response_model=List[Platform])
async def get_platforms(current_user: Dict = Depends(get_current_user)):
    """Get all platforms (admin feature)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM platforms ORDER BY created_at DESC")
    platforms = cursor.fetchall()
    conn.close()
    
    return [
        Platform(
            id=platform["id"],
            name=platform["name"],
            url=platform["url"],
            status=platform["status"],
            created_at=platform["created_at"]
        )
        for platform in platforms
    ]

@router.post("/platforms/", response_model=Platform, status_code=status.HTTP_201_CREATED)
async def create_platform(
    platform: PlatformCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new platform (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create platforms"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    
    platform_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO platforms (id, name, url, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (platform_id, platform.name, platform.url, platform.status, created_at))
    
    conn.commit()
    conn.close()
    
    logger.info(f"New platform created: {platform.name}")
    
    return Platform(
        id=platform_id,
        name=platform.name,
        url=platform.url,
        status=platform.status,
        created_at=created_at
    )

@router.delete("/platforms/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform(
    platform_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a platform (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete platforms"
        )
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found"
        )
    
    conn.commit()
    conn.close()
    
    logger.info(f"Platform deleted: {platform_id}")
    return None
