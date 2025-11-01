import sqlite3
import os
from logger_config import get_logger

logger = get_logger(__name__)


def integrity_check(db_path: str):
    """Run PRAGMA integrity_check on the SQLite database.

    Returns (ok: bool, message: str)
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        conn.close()
        if row:
            return (str(row[0]).lower() == 'ok', str(row[0]))
        return (False, 'no-result')
    except Exception as e:
        logger.exception("integrity_check failed for %s", db_path)
        return (False, str(e))


def backup_db(db_path: str, backup_path: str = None):
    """Create a binary backup of the SQLite database using the sqlite3 backup API.

    Returns (success: bool, path_or_error: str)
    """
    if backup_path is None:
        backup_path = db_path + '.bak'
    try:
        src = sqlite3.connect(db_path)
        dst = sqlite3.connect(backup_path)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        return (True, backup_path)
    except Exception as e:
        logger.exception("backup_db failed for %s -> %s", db_path, backup_path)
        return (False, str(e))


def remove_journal_if_exists(db_path: str):
    """Remove the -journal file if present (indicates a crashed session that didn't clean up).

    Returns True if removed, False otherwise.
    """
    journal = db_path + '-journal'
    try:
        if os.path.exists(journal):
            os.remove(journal)
            logger.info("Removed journal file: %s", journal)
            return True
        return False
    except Exception as e:
        logger.exception("Failed to remove journal file %s", journal)
        return False
