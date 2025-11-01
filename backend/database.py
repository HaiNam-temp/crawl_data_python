"""Database functions - giữ nguyên từ main.py"""
import sqlite3
import time
import hashlib
import uuid
from datetime import datetime
import json
import os

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
    # Increase timeout and allow connections from different threads
    # to reduce "database is locked" errors under concurrency.
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Use WAL mode to improve concurrency (allows concurrent readers and writers)
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        # If the PRAGMA fails (older SQLite builds), continue without crashing
        logger.warning("Could not set WAL mode on SQLite; continuing with defaults.")
    
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

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL,
            url TEXT UNIQUE,
            image TEXT,
            rating REAL,
            review_count INTEGER,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Ensure products table has expected columns (migrate older DBs)
    try:
        cursor.execute("PRAGMA table_info(products)")
        cols = [row[1] for row in cursor.fetchall()]
        # mapping of columns we expect and their SQL types
        expected = {
            'image': 'TEXT',
            'rating': 'REAL',
            'review_count': 'INTEGER',
            'metadata': 'TEXT',
            'created_at': 'TEXT'
        }
        for col, col_type in expected.items():
            if col not in cols:
                try:
                    logger.info("Altering products table to add missing column: %s %s", col, col_type)
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {col_type}")
                except Exception as e:
                    logger.error("Failed to add column %s to products table: %s", col, e, exc_info=True)
    except Exception as e:
        logger.error("Error checking/migrating products table schema: %s", e, exc_info=True)
    
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


def save_products(products: list) -> int:
    """Save a list of product dicts into the products table.

    Uses INSERT OR IGNORE on url uniqueness to avoid duplicates. Returns
    the number of rows inserted.
    """
    logger.info("Saving %d products to database.", len(products))
    try:
        db_exists = os.path.exists(DB_PATH)
        db_size = os.path.getsize(DB_PATH) if db_exists else 0
        logger.info("DB_PATH=%s exists=%s size=%d", DB_PATH, db_exists, db_size)
    except Exception as e:
        logger.warning("Could not stat DB_PATH %s: %s", DB_PATH, e)
    # Prefer a background single-writer queue if available to avoid write contention
    try:
        logger.debug("Attempting to import background db_writer to enqueue products")
        from backend import db_writer
        try:
            db_writer.enqueue_products(products)
            logger.info("Enqueued %d products to DB writer.", len(products))
            # Log queue size if available
            try:
                if hasattr(db_writer, '_writer') and hasattr(db_writer._writer, '_queue'):
                    qsize = db_writer._writer._queue.qsize()
                    logger.info("DB writer queue size after enqueue: %d", qsize)
            except Exception:
                pass
            return len(products)
        except Exception as e:
            logger.warning("Failed to enqueue products to DB writer, falling back to immediate write: %s", e, exc_info=True)
            # fallthrough to immediate write below
    except Exception as import_err:
        logger.debug("db_writer not importable or not available: %s", import_err)
        # db_writer not available; perform immediate writes
        pass

    # Immediate single-attempt writes (no retries). Log and skip on OperationalError.
    logger.info("Opening direct DB connection to %s", DB_PATH)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    except Exception as e:
        logger.exception("Failed to open DB connection to %s: %s", DB_PATH, e)
        return 0
    cursor = conn.cursor()
    inserted = 0
    for p in products:
        try:
            prod_id = str(uuid.uuid4())
            name = p.get('name') or p.get('title') or p.get('product_name') or ''
            price = p.get('price')
            url = p.get('url') or p.get('link') or ''
            image = p.get('image')
            rating = p.get('rating')
            review_count = p.get('review_count')
            metadata = None
            try:
                metadata = json.dumps(p.get('metadata') or {})
            except Exception:
                metadata = json.dumps({})
            created_at = datetime.utcnow().isoformat()

            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO products
                    (id, name, price, url, image, rating, review_count, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (prod_id, name, price, url, image, rating, review_count, metadata, created_at)
                )
                if cursor.rowcount > 0:
                    inserted += 1
                    try:
                        logger.info("Inserted product '%s' url=%s", name, url)
                    except Exception:
                        # logging shouldn't break the loop
                        pass
            except sqlite3.OperationalError as oe:
                # Log and skip if we can't write (e.g., database locked). Don't retry here.
                logger.warning("OperationalError saving product '%s': %s", name, oe)
                continue
        except Exception as e:
            logger.error("Failed to save product %s: %s", p.get('name'), e)
            continue

    conn.commit()
    conn.close()
    logger.info("Saved %d products to SQL database.", inserted)
    return inserted
