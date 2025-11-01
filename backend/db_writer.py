"""Simple single-writer background queue for SQLite writes.

This module provides a lightweight DB writer that serializes write requests
into a single thread/connection to avoid concurrent writers causing
"database is locked" errors.

Usage:
    from backend.db_writer import enqueue_products, start_db_writer, stop_db_writer
    start_db_writer()
    enqueue_products(list_of_product_dicts)
    stop_db_writer()
"""
import threading
import queue
import sqlite3
import time
from typing import List
from logger_config import get_logger
from backend.config import DB_PATH

logger = get_logger(__name__)


class DBWriter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop = threading.Event()

    def start(self):
        if not self._thread.is_alive():
            logger.info("Starting DBWriter thread")
            try:
                self._thread.start()
            except Exception as e:
                logger.exception("Failed to start DBWriter thread: %s", e)
        else:
            logger.debug("DBWriter thread already running")

    def stop(self, wait: float = 2.0):
        logger.info("Stopping DBWriter thread")
        self._stop.set()
        self._thread.join(timeout=wait)

    def enqueue(self, products: List[dict]):
        # Queue one batch (list of dicts) at a time
        try:
            before = self._queue.qsize()
        except Exception:
            before = -1
        self._queue.put(products)
        try:
            after = self._queue.qsize()
        except Exception:
            after = -1
        logger.info("Enqueued products batch (count=%d). queue before=%d after=%d", len(products), before, after)
        # Ensure thread is running
        if not self._thread.is_alive():
            self.start()

    def _run(self):
        try:
            db_exists = False
            try:
                db_exists = os.path.exists(self.db_path)
            except Exception:
                pass
            logger.info("DBWriter starting, DB_PATH=%s exists=%s", self.db_path, db_exists)
            conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
            cur = conn.cursor()
            logger.info("DBWriter connected to %s", self.db_path)
        except Exception as e:
            logger.exception("DBWriter failed to connect to DB %s: %s", self.db_path, e)
            return
        while not self._stop.is_set() or not self._queue.empty():
            try:
                batch = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            for p in batch:
                try:
                    prod_id = p.get('id') or p.get('url')
                    name = p.get('name')
                    price = p.get('price')
                    url = p.get('url')
                    image = p.get('image')
                    rating = p.get('rating')
                    review_count = p.get('review_count')
                    metadata = p.get('metadata') or ''
                    created_at = p.get('timestamp')

                    cur.execute(
                        """
                        INSERT OR IGNORE INTO products
                        (id, name, price, url, image, rating, review_count, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (prod_id, name, price, url, image, rating, review_count, metadata, created_at)
                    )
                    # Log per-product insertion success
                    try:
                        if cur.rowcount > 0:
                            logger.info("DBWriter: inserted product '%s' url=%s", name, url)
                        else:
                            logger.debug("DBWriter: product '%s' already exists or not inserted (url=%s)", name, url)
                    except Exception:
                        # rowcount access may not always be supported; ignore errors here
                        pass
                except sqlite3.OperationalError as oe:
                    logger.warning("DBWriter OperationalError saving product '%s': %s", p.get('name'), oe)
                    # skip this product
                    continue
                except Exception as e:
                    logger.exception("Unexpected error writing product: %s", e)
                    continue

            try:
                conn.commit()
                logger.info("DBWriter: committed batch of %d products", len(batch))
            except Exception as e:
                logger.exception("Failed to commit batch: %s", e)

            self._queue.task_done()

        try:
            conn.close()
        except Exception:
            pass
        logger.info("DBWriter stopped")


# Module-level writer instance
_writer = DBWriter(DB_PATH)


def start_db_writer():
    _writer.start()


def stop_db_writer():
    _writer.stop()


def enqueue_products(products: List[dict]):
    """Enqueue a list of product dicts for background writing.

    This function starts the writer if it isn't running yet.
    """
    _writer.enqueue(products)
