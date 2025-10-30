#!/usr/bin/env python3
"""Playwright-based scraper for dienthoaivui search pages.

This script renders the provided search URL and extracts product entries
directly from that page (does NOT follow other links). It uses a heuristic
similar to the Cellphones scraper: prefer product containers, but fall back
to anchors that have nearby price/image information.

Usage:
  python scripts/scrape_dienthoaivui_playwright_search.py --url "https://dienthoaivui.com.vn/tim-kiem?_tim_kiem=air" --limit 10
"""
import argparse
import json
import sys
import re
from urllib.parse import urljoin
from typing import List, Dict
from datetime import datetime

def scrape_dienthoaivui_products(product_name: str) -> List[Dict]:
    """
    Crawl sản phẩm từ Điện Thoại Vui và trả về list dict với format giống crawl_tiki_product
    Giới hạn chỉ lấy 5 sản phẩm
    """
    try:
        search_url = f"https://dienthoaivui.com.vn/tim-kiem?_tim_kiem={product_name}"
        raw_results = scrape(search_url, limit=10)  # Lấy 10 để có đủ data filter
        
        products = []
        current_time = datetime.now().isoformat()
        
        for idx, item in enumerate(raw_results, 1):
            if len(products) >= 5:  # Giới hạn 5 sản phẩm
                break
                
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
            product_id = f"dienthoaivui_{int(datetime.now().timestamp())}_{len(products)+1}"
            
            # Tạo product dict với format giống crawl_tiki_product
            product = {
                "id": product_id,
                "name": item.get('title', '').strip(),
                "price": price or 0,
                "original_price": price or 0,
                "discount": "Không giảm giá",
                "seller": "Điện Thoại Vui",
                "rating": f"{item.get('rating', 0.0):.1f}",
                "review_count": item.get('review_count', 0),
                "url": item.get('url', ''),
                "timestamp": current_time,
                "platform": "dienthoaivui",
                "sold_count": item.get('sold_count', "0")
            }
            
            # Thêm thông tin ảnh nếu có
            if item.get('image'):
                product["image"] = item.get('image')
            
            products.append(product)
        
        if products:
            print(f"Tìm thấy {len(products)} sản phẩm từ Điện Thoại Vui")
        else:
            print("Không tìm thấy sản phẩm nào từ Điện Thoại Vui")
        
        return products
        
    except Exception as e:
        print(f"Lỗi khi crawl dữ liệu từ Điện Thoại Vui: {e}")
        return []

def _clean_title(raw: str) -> str:
    if not raw:
        return ""
    for line in raw.splitlines():
        s = line.strip()
        if s:
            return s
    return raw.strip()

def _clean_price_text(text: str):
    if not text:
        return None
    m = re.search(r"(\d{1,3}(?:[\.,]\d{3})+(?:[\.,]\d+)?|\d{4,})", text.replace('\xa0',' '))
    if not m:
        return None
    s = m.group(1)
    cleaned = s.replace('.', '').replace(',', '')
    try:
        return float(cleaned)
    except Exception:
        return None

def scrape(search_url, limit=None):
    results = []
    try:
        import platform
        import asyncio
        if platform.system().startswith('Win'):
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass
    except Exception:
        pass

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(search_url, timeout=60000)
        # wait and scroll to trigger client-side rendering and lazy-load images
        page.wait_for_timeout(800)
        page.evaluate("() => { window.scrollTo(0, 0); }")
        page.wait_for_timeout(600)
        page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight/2); }")
        page.wait_for_timeout(800)
        page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
        page.wait_for_timeout(1200)

        # Prioritize anchors approach: DTV tends to render product links as anchors with images and prices
        anchors = page.query_selector_all('a[href]')
        seen = set()
        results_by_anchor = []
        size_re = __import__('re').compile(r"/(\d+)x(\d+)")
        price_re = __import__('re').compile(r"[\d\.,]+\s*(đ|₫|vnd)", __import__('re').I)

        def pick_title_from_text(text: str):
            if not text:
                return ''
            # prefer a line that looks like a name (not badge or price)
            for line in text.splitlines():
                s = line.strip()
                if not s:
                    continue
                # skip pure price lines or short badge lines
                if price_re.search(s):
                    continue
                if len(s) < 4:
                    continue
                # skip typical badge words
                if any(k in s.lower() for k in ('giảm', 'bảo hành', 'sắp về', 'smember', 'sale', '%')):
                    continue
                return s
            # fallback: first non-empty line
            for line in text.splitlines():
                if line.strip():
                    return line.strip()
            return text.strip()

        for a in anchors:
            if limit is not None and len(results_by_anchor) >= limit:
                break
            try:
                href = a.get_attribute('href') or ''
                if not href:
                    continue
                full = __import__('urllib.parse').urljoin(search_url, href)
                if full in seen:
                    continue
                # skip obvious non-product paths (articles, blog, booking)
                low = href.lower()
                if any(skip in low for skip in ('/tin-tuc', '/tin-tuc/', '/suachua', '/dat-lich', '/dich-vu', '/uu-dai')):
                    continue

                # evaluate ancestor innerText to find price and name lines
                text = (a.inner_text() or '').strip()
                anc_text = page.evaluate("(el) => { let n = el; let acc=''; for(let i=0;i<5;i++){ if(!n) break; if(n.innerText) acc = n.innerText + '\n' + acc; n = n.parentElement;} return acc; }", a) or ''
                # price detection: prefer ancestor block but also check anchor text itself
                pval = _clean_price_text(anc_text)
                if pval is None:
                    pval = _clean_price_text(text)

                # image detection: look for an img in the anchor or nearby ancestors/descendants
                try:
                    img_src = page.evaluate("(el)=>{ let i = el.querySelector('img'); if(i){ return i.getAttribute('src')||i.getAttribute('data-src')||i.getAttribute('data-lazy-src')||i.src;} let n = el.parentElement; for(let k=0;k<3;k++){ if(!n) break; let ii = n.querySelector('img'); if(ii) return ii.getAttribute('src')||ii.getAttribute('data-src')||ii.getAttribute('data-lazy-src')||ii.src; n = n.parentElement;} return ''; }", a) or ''
                except Exception:
                    img_src = ''
                img = __import__('urllib.parse').urljoin(search_url, img_src) if img_src else None
                has_large_img = False
                if img_src:
                    m = size_re.search(img_src)
                    if m:
                        try:
                            w = int(m.group(1)); h = int(m.group(2))
                            if max(w,h) >= 150:
                                has_large_img = True
                        except Exception:
                            pass

                # pick a robust title from ancestor block or anchor text
                title = pick_title_from_text(anc_text) or pick_title_from_text(text)
                if not title:
                    # try last resort: use entire anchor text cleaned
                    title = _clean_title(text)
                if not title:
                    continue

                # decide if likely a product: price present (in anc or anchor) or large image
                has_price = pval is not None
                if not (has_price or has_large_img):
                    # also accept if anchor text itself includes a price pattern
                    if not _clean_price_text(text):
                        continue

                seen.add(full)
                results_by_anchor.append({
                    'title': title, 
                    'url': full, 
                    'price': pval, 
                    'image': img,
                    'rating': 0.0,
                    'review_count': 0,
                    'sold_count': "0"
                })
            except Exception:
                continue

        # DEBUG: how many anchors passed heuristics
        try:
            print(f"anchors scanned -> {len(anchors)}, anchors matched -> {len(results_by_anchor)}")
        except Exception:
            pass

        if results_by_anchor:
            for it in results_by_anchor:
                if limit is not None and len(results) >= limit:
                    break
                results.append(it)
        else:
            # Try to find product-like containers first using common selectors
            item_selectors = ['.product-item', '.product-card', 'div.product', 'li.product', '.product-item-wrap']
            items = []
            for sel in item_selectors:
                try:
                    page.wait_for_selector(sel, timeout=1500)
                    items = page.query_selector_all(sel)
                    if items:
                        break
                except Exception:
                    continue

            # If we found item containers, extract from them
            if items:
                for item in items:
                    if limit is not None and len(results) >= limit:
                        break
                    try:
                        a = item.query_selector('a[href]')
                        if not a:
                            continue
                        href = a.get_attribute('href') or ''
                        url = urljoin(search_url, href)
                        if url in seen:
                            continue
                        seen.add(url)
                        # prefer explicit name/title elements inside the item
                        title = ''
                        try:
                            tnode = item.query_selector('.name-product, .product-name, .name, .title, h3, h2, h1, .product-title')
                            if tnode:
                                title = _clean_title(tnode.inner_text() or '')
                        except Exception:
                            title = ''
                        if not title:
                            title_raw = (a.inner_text() or '')
                            title = _clean_title(title_raw)

                        # image
                        img = None
                        img_el = item.query_selector('img') or a.query_selector('img')
                        if img_el:
                            src = img_el.get_attribute('src') or img_el.get_attribute('data-src') or img_el.get_attribute('data-lazy-src')
                            if src:
                                img = urljoin(search_url, src)

                        # price: look inside item for common price selectors, or fallback to regex
                        price = None
                        for ps in ['.price', '.product-price', '.gia', '.price-final_price', '[data-price]']:
                            try:
                                node = item.query_selector(ps)
                                if node:
                                    text = (node.get_attribute('data-price') or node.inner_text() or '').strip()
                                    pval = _clean_price_text(text)
                                    if pval:
                                        price = pval
                                        break
                            except Exception:
                                continue
                        if price is None:
                            whole = item.inner_text() or ''
                            price = _clean_price_text(whole)

                        # Tìm rating, review count và sold count trong item
                        rating = 0.0
                        review_count = 0
                        sold_count = "0"
                        
                        try:
                            item_text = item.inner_text() or ''
                            
                            # Tìm rating
                            import re
                            rating_patterns = [
                                r'(\d+\.?\d*)\s*/?\s*5\s*sao',
                                r'(\d+\.?\d*)\s*sao',
                                r'Rating:\s*(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*★'
                            ]
                            for pattern in rating_patterns:
                                rating_match = re.search(pattern, item_text, re.IGNORECASE)
                                if rating_match:
                                    try:
                                        rating_val = float(rating_match.group(1))
                                        if 0 <= rating_val <= 5:
                                            rating = rating_val
                                            break
                                    except ValueError:
                                        pass
                            
                            # Tìm review count
                            review_patterns = [
                                r'(\d+)\s*(?:đánh giá|review|nhận xét)',
                                r'\((\d+)\s*(?:đánh giá|review)\)',
                                r'(\d+)\s*comment'
                            ]
                            for pattern in review_patterns:
                                review_match = re.search(pattern, item_text, re.IGNORECASE)
                                if review_match:
                                    try:
                                        review_count = int(review_match.group(1))
                                        break
                                    except ValueError:
                                        pass
                            
                            # Tìm sold count
                            sold_patterns = [
                                r'(\d+[k\d,\.]*)\s*(?:đã bán|sold)',
                                r'Bán:\s*(\d+[k\d,\.]*)',
                                r'(\d+[k\d,\.]*)\s*lượt mua'
                            ]
                            for pattern in sold_patterns:
                                sold_match = re.search(pattern, item_text, re.IGNORECASE)
                                if sold_match:
                                    sold_count = sold_match.group(1)
                                    break
                                    
                        except Exception:
                            pass

                        results.append({
                            'title': title, 
                            'url': url, 
                            'price': price, 
                            'image': img,
                            'rating': rating,
                            'review_count': review_count,
                            'sold_count': sold_count
                        })
                    except Exception:
                        continue
            else:
                # Fallback: iterate anchors and pick those that have nearby price/image info
                anchors = page.query_selector_all('a[href]')
                for a in anchors:
                    if limit is not None and len(results) >= limit:
                        break
                    try:
                        href = a.get_attribute('href') or ''
                        if not href:
                            continue
                        url = urljoin(search_url, href)
                        if url in seen:
                            continue

                        # try to locate a nearby name element for cleaner product name
                        title = ''
                        try:
                            tnode = a.query_selector('.name-product, .product-name, .name, .title, h3, h2, h1, .product-title')
                            if tnode:
                                title = _clean_title(tnode.inner_text() or '')
                        except Exception:
                            title = ''
                        if not title:
                            title_raw = (a.inner_text() or '')
                            title = _clean_title(title_raw)
                        if not title or len(title) < 2:
                            # skip anchors without title-like text
                            continue

                        # find price by checking ancestors (up to 4 levels)
                        price = None
                        img = None
                        try:
                            ptext = page.evaluate("(a) => { let n=a; for(let i=0;i<4;i++){ if(!n) break; if(n.innerText && /[\\d\\.,]+\\s*(đ|₫|vnd)/i.test(n.innerText)) return n.innerText; n = n.parentElement; } return ''; }", a)
                            price = _clean_price_text(ptext)
                        except Exception:
                            price = None

                        # image inside anchor
                        try:
                            img_el = a.query_selector('img')
                            if img_el:
                                src = img_el.get_attribute('src') or img_el.get_attribute('data-src') or img_el.get_attribute('data-lazy-src')
                                if src:
                                    img = urljoin(search_url, src)
                        except Exception:
                            img = None

                        # Tìm rating và review count
                        rating = 0.0
                        review_count = 0
                        sold_count = "0"
                        
                        # Kiểm tra ancestor elements để tìm rating/review info
                        try:
                            ancestor_text = page.evaluate("(el) => { let n = el; let acc=''; for(let i=0;i<3;i++){ if(!n) break; if(n.innerText) acc += n.innerText + ' '; n = n.parentElement;} return acc; }", a) or ''
                            
                            # Tìm rating
                            import re
                            rating_patterns = [
                                r'(\d+\.?\d*)\s*/?\s*5\s*sao',
                                r'(\d+\.?\d*)\s*sao',
                                r'Rating:\s*(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*★'
                            ]
                            for pattern in rating_patterns:
                                rating_match = re.search(pattern, ancestor_text, re.IGNORECASE)
                                if rating_match:
                                    try:
                                        rating_val = float(rating_match.group(1))
                                        if 0 <= rating_val <= 5:
                                            rating = rating_val
                                            break
                                    except ValueError:
                                        pass
                            
                            # Tìm review count
                            review_patterns = [
                                r'(\d+)\s*(?:đánh giá|review|nhận xét)',
                                r'\((\d+)\s*(?:đánh giá|review)\)',
                                r'(\d+)\s*comment'
                            ]
                            for pattern in review_patterns:
                                review_match = re.search(pattern, ancestor_text, re.IGNORECASE)
                                if review_match:
                                    try:
                                        review_count = int(review_match.group(1))
                                        break
                                    except ValueError:
                                        pass
                            
                            # Tìm sold count
                            sold_patterns = [
                                r'(\d+[k\d,\.]*)\s*(?:đã bán|sold)',
                                r'Bán:\s*(\d+[k\d,\.]*)',
                                r'(\d+[k\d,\.]*)\s*lượt mua'
                            ]
                            for pattern in sold_patterns:
                                sold_match = re.search(pattern, ancestor_text, re.IGNORECASE)
                                if sold_match:
                                    sold_count = sold_match.group(1)
                                    break
                                    
                        except Exception:
                            pass

                        # keep anchors that have price or image
                        if price is None and not img:
                            continue

                        seen.add(url)
                        results.append({
                            'title': title, 
                            'url': url, 
                            'price': price, 
                            'image': img,
                            'rating': rating,
                            'review_count': review_count,
                            'sold_count': sold_count
                        })
                    except Exception:
                        continue

        try:
            browser.close()
        except Exception:
            pass

    # filter out obvious category/navigation entries: prefer items with price or
    # with product-sized images (not small 40x40 icons). Then dedupe and limit.
    filtered = []
    for r in results:
        img = (r.get('image') or '')
        price = r.get('price')
        # treat as product if price exists
        is_product = price is not None
        # or image seems to be a product image (not tiny icon)
        if not is_product and img:
            # cdni URLs include size like 40x40 or 300x300
            if re.search(r"/\d+x\d+", img):
                m = re.search(r"/(\d+)x(\d+)", img)
                if m:
                    try:
                        w = int(m.group(1))
                        h = int(m.group(2))
                        if max(w, h) >= 150:
                            is_product = True
                    except Exception:
                        pass
        # also ignore very short titles that look like badges
        title = (r.get('title') or '').strip()
        if not title or len(title) < 3:
            is_product = False

        if is_product:
            filtered.append(r)

    # dedupe by url and apply limit
    final = []
    seen_u = set()
    for r in filtered:
        u = r.get('url') or ''
        if u in seen_u:
            continue
        seen_u.add(u)
        final.append(r)
        if limit is not None and len(final) >= limit:
            break
    return final

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=False)
    parser.add_argument('--product', required=False)
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()

    if args.product:
        # Sử dụng function mới với format giống crawl_tiki_product
        res = scrape_dienthoaivui_products(args.product)
    elif args.url:
        # Sử dụng function cũ
        res = scrape(args.url, limit=args.limit)
    else:
        # Chế độ interactive
        print("Điện Thoại Vui Product Crawler")
        print("-" * 30)
        
        product_name = input("Nhập tên sản phẩm: ").strip()
        if not product_name:
            print("Tên sản phẩm không được để trống!")
            return
        
        res = scrape_dienthoaivui_products(product_name)
    
    import sys
    sys.stdout.buffer.write(json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8'))

if __name__ == '__main__':
    main()
