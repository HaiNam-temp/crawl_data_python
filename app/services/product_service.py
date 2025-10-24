from typing import List, Dict
import threading
import os
from app.repositories.product_repository import save_products, load_products
from Crawl_Data.crawl_iphones import crawl, load_shops


def get_products(file_name: str, limit: int = 0, offset: int = 0) -> Dict:
    items = load_products(file_name)
    total = len(items)
    if limit and limit > 0:
        items = items[offset: offset + limit]
    else:
        items = items[offset:]
    return {"total": total, "items": items}


def start_crawl_job(shop: str, pages: int, max_products: int, query: str, out: str, fetch_pages: bool):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    shops_path = os.path.join(project_root, "shops_example.json")
    shops = load_shops(shops_path)
    shop_conf = shops.get(shop, {})
    if max_products:
        shop_conf["max_products"] = max_products
    shop_conf["fetch_pages"] = fetch_pages

    def job():
        items = crawl(shop_conf, pages=pages, delay=1.0, query=query)
        save_products(out, items)

    t = threading.Thread(target=job, daemon=True)
    t.start()
    return {"status": "started", "out": out}
