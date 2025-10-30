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

# Note: on Windows the default event loop may not support subprocesses used by
# Playwright. Ensure the ProactorEventLoopPolicy is used when running on
# Windows so asyncio.create_subprocess_exec is implemented.
# We import Playwright inside the `scrape` function to avoid import-time side
# effects when the module is imported but Playwright isn't available.


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
                if img_el and img_el.get_attribute('src'):
                    img = urljoin(search_url, img_el.get_attribute('src'))
                # price not available in fallback anchors
                results.append({'title': title, 'url': product_url, 'price': None, 'image': img})
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
                results.append({'title': title, 'url': product_url, 'price': price, 'image': img})

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
    parser.add_argument('--url', required=True)
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()

    res = scrape(args.url, limit=args.limit)
    # Write UTF-8 bytes to stdout to avoid Windows console encoding errors (cp1252)
    import sys
    sys.stdout.buffer.write(json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8'))


if __name__ == '__main__':
    main()
