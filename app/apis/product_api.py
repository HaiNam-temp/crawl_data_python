from fastapi import APIRouter, HTTPException
from app.schemas.product_schema import ProductsResponse, CrawlRequest
from app.services.product_service import get_products, start_crawl_job

router = APIRouter(prefix="", tags=["Products"])


@router.get("/products", response_model=ProductsResponse)
def api_get_products(limit: int = 0, offset: int = 0, file: str = "iphones_tiki.json"):
    return get_products(file, limit, offset)


@router.post("/crawl")
def api_start_crawl(req: CrawlRequest):
    if req.pages <= 0:
        raise HTTPException(status_code=400, detail="pages must be > 0")
    return start_crawl_job(req.shop, req.pages, req.max_products, req.query, req.out, req.fetch_pages)
