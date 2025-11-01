"""Product routes - expose products stored in the SQLite DB

Endpoints:
- GET /products/        -> list products, optional q (search), limit, offset
- GET /products/{id}    -> get single product by id

These are intentionally public (no auth) so the frontend can query persisted
crawl results. Keep implementations simple and use the existing `get_db()`
helper and `Product` Pydantic model for responses.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import json

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from ..database import get_db
from ..models import Product

router = APIRouter(prefix="/products")


@router.get("/", response_model=List[Product])
async def list_products(q: Optional[str] = Query(None), limit: int = 50, offset: int = 0):
    """List products stored in the database.

    Optional query `q` performs a simple LIKE search against name and url.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        if q:
            like = f"%{q}%"
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? OR url LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (like, like, limit, offset)
            )
        else:
            cursor.execute(
                "SELECT * FROM products ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )

        rows = cursor.fetchall()
        results = []
        for r in rows:
            # Safe column accessor (older DBs might lack some columns)
            def safe_get(key):
                try:
                    return r[key]
                except Exception:
                    return None

            # metadata is stored as JSON string in DB
            metadata_val = safe_get("metadata")
            metadata = None
            try:
                metadata = json.loads(metadata_val) if metadata_val else None
            except Exception:
                metadata = None

            results.append(Product(
                id=safe_get("id") or "",
                name=safe_get("name") or "",
                price=safe_get("price"),
                url=safe_get("url") or "",
                image=safe_get("image"),
                rating=safe_get("rating"),
                review_count=safe_get("review_count"),
                metadata=metadata,
                created_at=safe_get("created_at") or ""
            ))

        return results
    finally:
        conn.close()


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Return a single product by ID."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        r = cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Product not found")

        def safe_get(key):
            try:
                return r[key]
            except Exception:
                return None

        metadata_val = safe_get("metadata")
        metadata = None
        try:
            metadata = json.loads(metadata_val) if metadata_val else None
        except Exception:
            metadata = None

        return Product(
            id=safe_get("id") or "",
            name=safe_get("name") or "",
            price=safe_get("price"),
            url=safe_get("url") or "",
            image=safe_get("image"),
            rating=safe_get("rating"),
            review_count=safe_get("review_count"),
            metadata=metadata,
            created_at=safe_get("created_at") or ""
        )
    finally:
        conn.close()
