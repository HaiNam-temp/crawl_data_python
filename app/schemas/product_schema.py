from pydantic import BaseModel
from typing import Optional, List


class Product(BaseModel):
    title: str
    price: Optional[float]
    link: Optional[str]
    seller: Optional[str]
    image: Optional[str]


class ProductsResponse(BaseModel):
    total: int
    items: List[Product]


class CrawlRequest(BaseModel):
    pages: int
    max_products: Optional[int] = 0
    shop: Optional[str] = "tiki"
    query: Optional[str] = "iphone"
    out: Optional[str] = "iphones_tiki.json"
    fetch_pages: Optional[bool] = False
