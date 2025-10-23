"""
Simple crawler for iPhone listings using requests + BeautifulSoup.
Configure shop selectors in `shops_example.json`.
Outputs CSV or JSON.
"""
import argparse
import csv
import json
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch(url: str, timeout: int = 10) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp


def parse_listing(html: str, selectors: Dict[str, str], base_url: str = None) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    list_selector = selectors.get("list")
    if not list_selector:
        return items

    for el in soup.select(list_selector):
        try:
            title_el = el.select_one(selectors.get("title", ""))
            price_el = el.select_one(selectors.get("price", ""))
            link_el = el.select_one(selectors.get("link", "a"))
            seller_el = el.select_one(selectors.get("seller", ""))

            title = title_el.get_text(strip=True) if title_el else ""
            price = price_el.get_text(strip=True) if price_el else ""
            link = link_el.get("href") if link_el else None
            if link and base_url:
                # make relative links absolute
                link = urljoin(base_url, link)
            seller = seller_el.get_text(strip=True) if seller_el else ""
            image_el = el.select_one(selectors.get("image", "")) if selectors else None
            image = None
            if image_el:
                # try src or data-src
                image = image_el.get("src") or image_el.get("data-src") or None
                if image and base_url:
                    image = urljoin(base_url, image)

            items.append({
                "title": title,
                "price": price,
                "link": link,
                "seller": seller,
                "image": image,
            })
        except Exception:
            # ignore single item parse failures
            continue

    return items


def is_json_response(resp: requests.Response) -> bool:
    ct = resp.headers.get("Content-Type", "")
    if "application/json" in ct:
        return True
    text = resp.text.lstrip()
    return text.startswith("{") or text.startswith("[")


def extract_products_from_json(obj, base_url: str = None) -> List[Dict]:
    """Recursively search JSON and return product-like dicts with keys link, image, title, price when possible."""
    products: List[Dict] = []

    def _walk(o):
        if isinstance(o, dict):
            # heuristics: if dict looks like a product
            keys_lower = {k.lower(): v for k, v in o.items()}
            link = None
            image = None
            title = None
            price = None

            # common url fields
            for k in ("url", "product_url", "link", "path", "url_path"):
                if k in keys_lower and isinstance(keys_lower[k], str):
                    link = keys_lower[k]
                    break

            # image fields
            for k in ("thumbnail_url", "thumbnail", "image", "image_url", "images"):
                if k in keys_lower:
                    v = keys_lower[k]
                    if isinstance(v, str):
                        image = v
                        break
                    elif isinstance(v, list) and v:
                        image = v[0]
                        break

            # title/price
            for k in ("name", "title", "product_name"):
                if k in keys_lower and isinstance(keys_lower[k], str):
                    title = keys_lower[k]
                    break
            for k in ("price", "current_price", "final_price", "list_price"):
                if k in keys_lower and (isinstance(keys_lower[k], int) or isinstance(keys_lower[k], float) or (isinstance(keys_lower[k], str) and keys_lower[k].strip().isdigit())):
                    price = keys_lower[k]
                    break

            if link:
                # normalize
                if isinstance(link, str) and base_url:
                    link = urljoin(base_url, link)
                products.append({"link": link, "image": image, "title": title, "price": price})

            # continue walking child values for nested products
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for item in o:
                _walk(item)

    _walk(obj)
    return products


# Note: extract_products_from_json(obj, base_url) is defined above and used to pull
# link/image/title/price from typical API JSON shapes. The duplicate/older
# implementation was removed to avoid confusion.


def parse_product_page(html: str, selectors: Dict[str, str], base_url: str = None) -> Dict:
    
    soup = BeautifulSoup(html, "html.parser")
    # title
    title = ""
    price = ""
    seller = ""

    if selectors:
        title_sel = selectors.get("title")
        price_sel = selectors.get("price")
        seller_sel = selectors.get("seller")
        if title_sel:
            el = soup.select_one(title_sel)
            if el:
                title = el.get_text(strip=True)
        if price_sel:
            el = soup.select_one(price_sel)
            if el:
                price = el.get_text(strip=True)
        if seller_sel:
            el = soup.select_one(seller_sel)
            if el:
                seller = el.get_text(strip=True)

    # fallbacks using meta tags
    if not title:
        og = soup.select_one('meta[property="og:title"]') or soup.select_one('meta[name="title"]')
        if og and og.get("content"):
            title = og.get("content").strip()

    if not price:
        # common meta for price
        meta_price = soup.select_one('meta[property="product:price:amount"]') or soup.select_one('meta[name="price"]')
        if meta_price and meta_price.get("content"):
            price = meta_price.get("content").strip()
        else:
            # try to find a number with currency nearby
            txt = soup.get_text(separator=" ")
            m = re.search(r"([\d\.,]+)\s*(₫|VND|đ|USD|VNĐ)", txt)
            if m:
                price = m.group(1) + " " + m.group(2)

    if not seller:
        og_site = soup.select_one('meta[property="og:site_name"]')
        if og_site and og_site.get("content"):
            seller = og_site.get("content").strip()

    # try og:image
    image = ""
    og_img = soup.select_one('meta[property="og:image"]') or soup.select_one('link[rel="image_src"]')
    if og_img and og_img.get("content"):
        image = og_img.get("content").strip()
    else:
        # try first product image
        img = soup.select_one('img')
        if img and img.get("src"):
            image = img.get("src")

    if image and base_url:
        image = urljoin(base_url, image)

    return {"title": title, "price": price, "link": base_url, "seller": seller, "image": image}


def crawl(shop_conf: Dict, pages: int = 1, delay: float = 1.0, query: str = None) -> List[Dict]:
    results = []
    base_url = shop_conf.get("url")
    selectors = shop_conf.get("selectors", {})

    for page in range(1, pages + 1):
        # Support URLs with named {page} or positional {} placeholders (e.g. API: q={} & page={})
        try:
            url = base_url.format(page=page)
        except (IndexError, KeyError):
            # fallback to positional formatting
            q = query or shop_conf.get("query") or "iphone"
            try:
                url = base_url.format(q, page)
            except Exception:
                # last resort: try to replace literal tokens
                url = base_url.replace("{page}", str(page)).replace("{}", str(page)).replace("{q}", q)
        print(f"Fetching {url}")
        resp = fetch(url)

        # If the search endpoint returns JSON (API), try to extract product info directly from JSON
        if is_json_response(resp):
            try:
                j = resp.json()
                products = extract_products_from_json(j)
                if products:
                    # limit products if configured
                    max_products = shop_conf.get("max_products") or 0
                    if max_products:
                        products = products[:max_products]
                    print(f"  Parsed {len(products)} products directly from JSON on page {page}")
                    results.extend([{**p, "link": urljoin(url, p.get("link") or "")} for p in products])
                else:
                    # fallback: try to find product-like entries (with link) in JSON
                    candidates = extract_products_from_json(j, base_url=url)
                    if candidates:
                        fetch_pages = shop_conf.get("fetch_pages", False)
                        max_fetch = shop_conf.get("max_fetch", 10)
                        resolved = []
                        count = 0
                        for c in candidates:
                            link = c.get("link")
                            if fetch_pages and count >= max_fetch:
                                break
                            if fetch_pages and link:
                                try:
                                    p_resp = fetch(link)
                                    prod = parse_product_page(p_resp.text, selectors, base_url=link)
                                    resolved.append(prod)
                                    count += 1
                                    time.sleep(0.3)
                                except Exception:
                                    # keep the entry with whatever data we have
                                    resolved.append({"title": c.get("title") or "", "price": c.get("price") or "", "link": link, "seller": "", "image": c.get("image")})
                            else:
                                resolved.append({"title": c.get("title") or "", "price": c.get("price") or "", "link": link, "seller": "", "image": c.get("image")})
                        print(f"  Extracted {len(resolved)} product candidates from JSON on page {page}")
                        results.extend(resolved)
                    else:
                        print("  No product data found in JSON response")
            except Exception:
                print("  Failed to parse JSON response")
        else:
            items = parse_listing(resp.text, selectors, base_url=url)
            print(f"  Found {len(items)} items on page {page}")
            results.extend(items)
        time.sleep(delay)
    return results


def save_csv(items: List[Dict], path: str):
    if not items:
        print("No items to save")
        return
    keys = list(items[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(items)
    print(f"Saved CSV to {path}")


def save_json(items: List[Dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to {path}")


def load_shops(path: str) -> Dict[str, Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Crawl iPhone listings from configured shops")
    parser.add_argument("shop", help="Shop key from shops config (e.g. shop1)")
    parser.add_argument("--shops-file", default="shops_example.json", help="Path to shops config JSON")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to crawl")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--out", default="out.csv", help="Output file (json or csv)")
    parser.add_argument("--query", "-q", default=None, help="Search query (used for API-style endpoints)")
    parser.add_argument("--fetch-pages", action="store_true", help="When JSON is returned, fetch product pages to parse details")
    parser.add_argument("--max-products", type=int, default=0, help="Limit products parsed directly from JSON (0 = no limit)")
    parser.add_argument("--max-fetch", type=int, default=10, help="Max number of individual product pages to fetch when --fetch-pages is used")
    args = parser.parse_args()

    shops = load_shops(args.shops_file)
    if args.shop not in shops:
        print(f"Shop '{args.shop}' not found in {args.shops_file}")
        return

    # pass CLI options into shop config overrides
    shop_conf = shops[args.shop]
    # allow CLI to override config
    if args.fetch_pages:
        shop_conf["fetch_pages"] = True
    if args.max_products:
        shop_conf["max_products"] = args.max_products
    if args.max_fetch:
        shop_conf["max_fetch"] = args.max_fetch

    items = crawl(shop_conf, pages=args.pages, delay=args.delay, query=args.query)

    # If user provided a relative path, save it relative to the script directory
    out_path = args.out
    if not (out_path.startswith("/") or out_path.startswith("\\") or ":" in out_path):
        # relative path -> place next to this script
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(script_dir, out_path)

    if out_path.lower().endswith(":json") or out_path.lower().endswith(".json"):
        save_json(items, out_path)
    else:
        save_csv(items, out_path)


if __name__ == "__main__":
    main()
