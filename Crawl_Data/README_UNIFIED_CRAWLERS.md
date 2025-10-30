# Unified Product Crawlers

Hệ thống crawler tổng hợp để tìm kiếm sản phẩm từ nhiều trang web thương mại điện tử.

## Các trang web được hỗ trợ

1. **Tiki.vn** - API crawling
2. **Lazada.vn** - Selenium crawling  
3. **CellphoneS.com.vn** - Playwright crawling
4. **DienThoaiVui.com.vn** - Playwright crawling

## Cấu trúc dữ liệu đầu ra

Tất cả crawler đều trả về format dữ liệu thống nhất:

```json
{
  "id": "unique_product_id",
  "name": "Tên sản phẩm",
  "price": 15000000,
  "original_price": 16000000,
  "discount": "-6%",
  "seller": "Tên shop/seller",
  "rating": "4.5",
  "review_count": 123,
  "url": "https://link-to-product",
  "timestamp": "2025-10-30T10:00:00",
  "platform": "tiki/lazada/cellphones/dienthoaivui"
}
```

## Cách sử dụng

### 1. Chạy tất cả crawler cùng lúc (Khuyến nghị)

```bash
# Chế độ interactive
python run_all_crawlers.py

# Hoặc với tham số
python run_all_crawlers.py "iPhone 13"
```

### 2. Chạy từng crawler riêng lẻ

#### Tiki
```python
from crawl_tiki_product import crawl_tiki_product
products = crawl_tiki_product("iPhone 13")
```

#### Lazada
```python
from lazada_crawler_complete import LazadaCrawler
crawler = LazadaCrawler()
products = crawler.crawl_lazada_products("iPhone 13")
```

#### CellphoneS
```python
from scrape_cellphones_playwright import scrape_cellphones_products
products = scrape_cellphones_products("iPhone 13")
```

#### Điện Thoại Vui
```python
from scrape_dienthoaivui_playwright_search import scrape_dienthoaivui_products
products = scrape_dienthoaivui_products("iPhone 13")
```

## Output của run_all_crawlers.py

Khi chạy file chính, bạn sẽ nhận được:

1. **Báo cáo console** - Thống kê tổng quan
2. **File JSON** - Kết quả chi tiết (tùy chọn)
3. **Dữ liệu structured** - Format JSON chuẩn

### Ví dụ báo cáo console:

```
============================================================
           BÁO CÁO TỔNG HỢP CRAWLER
============================================================
Từ khóa tìm kiếm: iPhone 13
Thời gian thực hiện: 12.5 giây
Tổng số sản phẩm: 28
------------------------------------------------------------
✓ Tiki           :   5 sản phẩm
✓ Lazada         :  12 sản phẩm
✓ CellphoneS     :   7 sản phẩm
✓ Điện Thoại Vui :   4 sản phẩm
============================================================
```

## Yêu cầu hệ thống

### Dependencies cần thiết:
```bash
pip install requests beautifulsoup4 selenium playwright webdriver-manager
```

### Cài đặt Playwright browsers:
```bash
playwright install chromium
```

## Tính năng nổi bật

- ✅ **Crawling đồng thời** - Tất cả các trang web được crawl song song
- ✅ **Format dữ liệu thống nhất** - Dễ dàng xử lý và phân tích
- ✅ **Error handling** - Xử lý lỗi graceful, không crash
- ✅ **Logging chi tiết** - Theo dõi quá trình crawling
- ✅ **Headless mode** - Crawler chạy nền, không mở browser
- ✅ **Export JSON** - Lưu kết quả vào file

## Cách thức hoạt động

1. **Input**: Tên sản phẩm cần tìm
2. **Processing**: 
   - Tạo 4 threads để crawl song song
   - Mỗi thread chạy một crawler cụ thể
   - Chuẩn hóa dữ liệu về format thống nhất
3. **Output**: 
   - Báo cáo tổng hợp
   - Danh sách sản phẩm đã được chuẩn hóa
   - File JSON (tùy chọn)

## Troubleshooting

### Lỗi thường gặp:

1. **Playwright lỗi**: Cài đặt browsers
   ```bash
   playwright install
   ```

2. **Selenium lỗi**: Kiểm tra ChromeDriver
   ```bash
   pip install webdriver-manager
   ```

3. **Import lỗi**: Kiểm tra logger_config.py
   - File này phải tồn tại trong thư mục gốc

## Mở rộng

Để thêm crawler mới:

1. Tạo function với format output giống `crawl_tiki_product`
2. Thêm vào `run_all_crawlers.py` trong danh sách `crawlers`
3. Update README

## Hiệu suất

- **Thời gian trung bình**: 10-15 giây cho 4 trang web
- **Số sản phẩm**: 20-40 sản phẩm per search
- **Memory usage**: ~100-200MB
- **Network**: Phụ thuộc vào tốc độ mạng

## License

MIT License - Sử dụng tự do cho mục đích học tập và nghiên cứu.