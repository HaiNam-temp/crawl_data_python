Crawl iPhone listings using BeautifulSoup

Files
- crawl_iphones.py - main crawler script (requests + BeautifulSoup).
- shops_example.json - sample shop configurations. Update selectors to match the shop's HTML.
- requirements.txt - Python dependencies.

Usage
1. Create a virtual environment and install deps:

   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

2. Edit `shops_example.json` and add the real shop key with correct `url` and `selectors`.
   - `url` can include `{page}` which will be replaced by page numbers.
   - `selectors` must include `list` for item container and optional `title`, `price`, `link`, `seller` CSS selectors.

3. Run:

   python crawl_iphones.py example_shop --pages 2 --out iphones.json

Notes
- This simple crawler works for server-rendered pages. For JavaScript-heavy sites (Shopee, Lazada, Tiki) use Selenium or Playwright.
- Respect site robots.txt and terms of service. Add delays and caching to avoid overloading servers.
