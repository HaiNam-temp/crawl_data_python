"""Database functions - giữ nguyên từ main.py"""
import sqlite3
import hashlib
import uuid
from datetime import datetime

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from .config import DB_PATH

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    """)
    
    # Platforms table (for admin)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        )
    """)
    
    # Create or update default admin account
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    existing_admin = cursor.fetchone()
    
    if existing_admin:
        # Cập nhật tài khoản admin hiện tại để đảm bảo có quyền admin
        admin_password_hash = hash_password("admin")
        cursor.execute("""
            UPDATE users 
            SET is_admin = 1, 
                password_hash = ?,
                email = 'admin@example.com'
            WHERE username = 'admin'
        """, (admin_password_hash,))
        logger.info("Admin account updated (username: admin, password: admin)")
    else:
        # Tạo tài khoản admin mới
        admin_id = str(uuid.uuid4())
        admin_password_hash = hash_password("admin")
        created_at = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, full_name, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (admin_id, "admin", "admin@example.com", admin_password_hash, "Administrator", 1, created_at))
        logger.info("Default admin account created (username: admin, password: admin)")
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")
