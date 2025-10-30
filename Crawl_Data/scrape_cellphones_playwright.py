#!/usr/bin/env python3
"""Simple Playwright scraper for cellphones.com.vn search pages.

Usage:
  python scripts/scrape_cellphones_playwright.py --url "https://cellphones.com.vn/catalogsearch/result?q=air" --limit 10

This script renders the page with Chromium, waits for product items, and extracts:
  - title
  - url
  - price (if present)
  - image

"""
import argparse
import json
from urllib.parse import urljoin
import sys
import asyncio
from typing import List, Dict
from datetime import datetime

# Removed logger dependencies

# Note: on Windows the default event loop may not support subprocesses used by
# Playwright. Ensure the ProactorEventLoopPolicy is used when running on
# Windows so asyncio.create_subprocess_exec is implemented.
# We import Playwright inside the `scrape` function to avoid import-time side
# effects when the module is imported but Playwright isn't available.


def scrape_cellphones_products(product_name: str) -> List[Dict]:
    """
    Crawl sản phẩm từ CellphoneS và trả về list dict với format giống crawl_tiki_product
    Giới hạn chỉ lấy 5 sản phẩm
    """
    try:
        search_url = f"https://cellphones.com.vn/catalogsearch/result?q={product_name}"
        raw_results = scrape(search_url, limit=5)  # Giới hạn 5 sản phẩm
        
        products = []
        current_time = datetime.now().isoformat()
        
        for idx, item in enumerate(raw_results[:5], 1):  # Đảm bảo chỉ lấy 5 sản phẩm
            if not item.get('title'):
                continue
            
            # Xử lý giá
            price = item.get('price', 0)
            if isinstance(price, str):
                # Trích xuất số từ string
                import re
                price_numbers = re.findall(r'[\d,\.]+', price.replace('₫', '').replace('đ', ''))
                if price_numbers:
                    try:
                        price_str = price_numbers[0].replace(',', '').replace('.', '')
                        price = int(price_str)
                    except (ValueError, IndexError):
                        price = 0
            
            # Tạo unique product ID
            product_id = f"cellphones_{int(datetime.now().timestamp())}_{idx}"
            
            # Tạo product dict với format giống crawl_tiki_product
            product = {
                "id": product_id,
                "name": item.get('title', '').strip(),
                "price": price or 0,
                "original_price": price or 0,
                "discount": "Không giảm giá",
                "seller": "CellphoneS",
                "rating": f"{item.get('rating', 0.0):.1f}",
                "review_count": item.get('review_count', 0),
                "url": item.get('url', ''),
                "timestamp": current_time,
                "platform": "cellphones",
                "sold_count": item.get('sold_count', "0")
            }
            
            # Thêm thông tin ảnh nếu có
            if item.get('image'):
                product["image"] = item.get('image')
            
            products.append(product)
        
        # Đảm bảo chỉ trả về tối đa 5 sản phẩm
        products = products[:5]
        
        if products:
            print(f"Tìm thấy {len(products)} sản phẩm từ CellphoneS")
        else:
            print("Không tìm thấy sản phẩm nào từ CellphoneS")
        
        return products
        
    except Exception as e:
        print(f"Lỗi khi crawl dữ liệu từ CellphoneS: {e}")
        return []


def scrape(search_url, limit=None):
    results = []

    # On Windows ensure Proactor event loop policy so subprocess support exists.
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            # If setting policy fails, continue and let Playwright raise a clearer error
            pass

    # Import Playwright here to delay heavy imports and avoid failing at module
    # import time in environments without Playwright installed.
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(search_url, timeout=60000)

        # Wait for some product-like elements to appear. Try several selectors.
        selectors = [".product-item", "a.product-item-link", "div.product-item-info", ".product-card"]
        found = False
        for sel in selectors:
            try:
                page.wait_for_selector(sel, timeout=3000)
                found = True
                break
            except Exception:
                continue

        # If none found, still proceed and try to collect anchors
        # Prefer selecting whole product items and then extracting details inside each item
        item_selectors = ['.product-item', 'div.product-item-info', '.product-card', '.product-item-wrap']
        items = []
        for sel in item_selectors:
            items = page.query_selector_all(sel)
            if items:
                break

        # fallback: anchors that look like product links
        if not items:
            anchors = page.query_selector_all('a.product-item-link, a[href$=".html"]')
            for a in anchors:
                if limit is not None and len(results) >= limit:
                    break
                href = a.get_attribute('href')
                if not href:
                    continue
                product_url = urljoin(search_url, href)
                title_raw = (a.inner_text() or '')
                title = _clean_title(title_raw)
                img = None
                img_el = a.query_selector('img')
                if item.get('image'):
                    img = urljoin(search_url, item.get('image'))
                # price not available in fallback anchors
                results.append({
                    'title': title, 
                    'url': product_url, 
                    'price': None, 
                    'image': img,
                    'rating': 0.0,
                    'review_count': 0,
                    'sold_count': "0"
                })
        else:
            for item in items:
                if limit is not None and len(results) >= limit:
                    break
                a = item.query_selector('a.product-item-link') or item.query_selector('a[href]')
                if not a:
                    continue
                href = a.get_attribute('href')
                if not href:
                    continue
                product_url = urljoin(search_url, href)
                title_raw = (a.inner_text() or '')
                if title_raw.strip():
                    title = _clean_title(title_raw)
                else:
                    title = _clean_title(item.get_attribute('data-name') or '')

                # image
                img = None
                img_el = item.query_selector('img')
                if img_el and img_el.get_attribute('src'):
                    img = urljoin(search_url, img_el.get_attribute('src'))

                # price
                price = None
                for ps in ['.price', '.product-price', '.price-final_price', '.price-box', '[data-price]']:
                    node = item.query_selector(ps)
                    if node:
                        text = (node.get_attribute('data-price') or node.inner_text() or '').strip()
                        cleaned = ''.join(ch for ch in text if ch.isdigit() or ch in ',.')
                        if cleaned:
                            try:
                                price = float(cleaned.replace(',', ''))
                            except Exception:
                                price = None
                            break
                
                # rating và review count
                rating = 0.0
                review_count = 0
                sold_count = "0"
                
                # Tìm rating trong item
                rating_selectors = ['.rating', '.star-rating', '.review-star', '.rating-average', '[data-rating]']
                for rs in rating_selectors:
                    rating_node = item.query_selector(rs)
                    if rating_node:
                        rating_text = rating_node.inner_text() or rating_node.get_attribute('data-rating') or ''
                        import re
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            try:
                                rating_val = float(rating_match.group(1))
                                if 0 <= rating_val <= 5:
                                    rating = rating_val
                                    break
                            except ValueError:
                                pass
                
                # Tìm review count trong item
                review_selectors = ['.review-count', '.reviews', '.comment-count', '.rating-count']
                for rs in review_selectors:
                    review_node = item.query_selector(rs)
                    if review_node:
                        review_text = review_node.inner_text() or ''
                        import re
                        review_match = re.search(r'(\d+)', review_text)
                        if review_match:
                            try:
                                review_count = int(review_match.group(1))
                                break
                            except ValueError:
                                pass
                
                # Tìm sold count trong item
                sold_selectors = ['.sold', '.sold-count', '.purchase-count', '.buy-count']
                for ss in sold_selectors:
                    sold_node = item.query_selector(ss)
                    if sold_node:
                        sold_text = sold_node.inner_text() or ''
                        # Lấy text chứa "đã bán" hoặc "sold"
                        import re
                        sold_match = re.search(r'(\d+[k\d,\.]*)\s*(?:đã bán|sold)', sold_text, re.IGNORECASE)
                        if sold_match:
                            sold_count = sold_match.group(1)
                            break
                
                # fallback: try to extract first number with currency from whole item text
                if price is None:
                    import re
                    whole = (item.inner_text() or '')
                    # look for patterns like 1.090.000đ or 740.000đ or 1290000
                    m = re.search(r"(\d{1,3}(?:[\.,]\d{3})+(?:[\.,]\d+)?|\d{4,})\s*(?:đ|₫|VND|vnđ)?", whole)
                    if m:
                        num = m.group(1)
                        num_clean = num.replace('.', '').replace(',', '')
                        try:
                            price = float(num_clean)
                        except Exception:
                            price = None
                            
                # Fallback: tìm rating/review trong toàn bộ text của item
                if rating == 0.0 or review_count == 0:
                    whole_text = item.inner_text() or ''
                    if rating == 0.0:
                        import re
                        rating_patterns = [
                            r'(\d+\.?\d*)\s*/?\s*5\s*sao',
                            r'(\d+\.?\d*)\s*sao',
                            r'Rating:\s*(\d+\.?\d*)',
                            r'(\d+\.?\d*)\s*★'
                        ]
                        for pattern in rating_patterns:
                            rating_match = re.search(pattern, whole_text, re.IGNORECASE)
                            if rating_match:
                                try:
                                    rating_val = float(rating_match.group(1))
                                    if 0 <= rating_val <= 5:
                                        rating = rating_val
                                        break
                                except ValueError:
                                    pass
                    
                    if review_count == 0:
                        import re
                        review_patterns = [
                            r'(\d+)\s*(?:đánh giá|review|nhận xét)',
                            r'\((\d+)\s*(?:đánh giá|review)\)',
                            r'(\d+)\s*comment'
                        ]
                        for pattern in review_patterns:
                            review_match = re.search(pattern, whole_text, re.IGNORECASE)
                            if review_match:
                                try:
                                    review_count = int(review_match.group(1))
                                    break
                                except ValueError:
                                    pass
                                    
                results.append({
                    'title': title, 
                    'url': product_url, 
                    'price': price, 
                    'image': img,
                    'rating': rating,
                    'review_count': review_count,
                    'sold_count': sold_count
                })

        browser.close()
    return results

def _clean_title(raw: str) -> str:
    """Return the first non-empty line from raw text, trimmed.

    This helps when sites include price/discounts/newlines in the same
    element as the product name. If no non-empty line is found, return
    the fully-stripped input.
    """
    if not raw:
        return ""
    # splitlines handles \r\n and variations
    for line in raw.splitlines():
        s = line.strip()
        if s:
            return s
    return raw.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=False)
    parser.add_argument('--product', required=False)
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()

    if args.product:
        # Sử dụng function mới với format giống crawl_tiki_product
        res = scrape_cellphones_products(args.product)
    elif args.url:
        # Sử dụng function cũ
        res = scrape(args.url, limit=args.limit)
    else:
        # Chế độ interactive
        print("CellphoneS Product Crawler")
        print("-" * 30)
        
        product_name = input("Nhập tên sản phẩm: ").strip()
        if not product_name:
            print("Tên sản phẩm không được để trống!")
            return
        
        res = scrape_cellphones_products(product_name)
    
    # Write UTF-8 bytes to stdout to avoid Windows console encoding errors (cp1252)
    import sys
    sys.stdout.buffer.write(json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8'))


if __name__ == '__main__':
    main()
