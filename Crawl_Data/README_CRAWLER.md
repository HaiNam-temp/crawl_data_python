# Multi-Platform Crawler Usage Guide

## 📋 Mô tả
File `run_all_crawlers.py` cho phép chạy tất cả 4 crawler cùng lúc:
- **Tiki** (API-based)
- **Lazada** (Selenium-based) 
- **Cellphones** (Playwright-based)
- **DienThoaiVui** (Playwright-based)

## 🚀 Cách sử dụng

### 1. Chạy tất cả platforms
```bash
python run_all_crawlers.py --query "iPhone 15" --limit 10
```

### 2. Chạy platforms cụ thể
```bash
python run_all_crawlers.py --query "Samsung Galaxy" --platforms tiki lazada --limit 5
```

### 3. Lưu kết quả vào file cụ thể
```bash
python run_all_crawlers.py --query "laptop dell" --output "laptop_results.json" --limit 20
```

### 4. Các options đầy đủ
```bash
python run_all_crawlers.py \
  --query "MacBook Pro" \
  --limit 15 \
  --platforms tiki cellphones \
  --output "macbook_crawl.json"
```

## 📊 Kết quả

### Console Output
```
==============================================================
CRAWL SUMMARY
==============================================================
Query: iPhone 15
Duration: 45.32 seconds
Total Products: 28

Per Platform:
  ✓ Tiki: 10 products
  ✓ Lazada: 8 products
  ✓ Cellphones: 6 products
  ✓ Dienthoaivui: 4 products
==============================================================
```

### JSON File Structure
```json
{
  "query": "iPhone 15",
  "timestamp": "2025-10-30T10:30:00",
  "duration_seconds": 45.32,
  "total_products": 28,
  "platforms": {
    "tiki": [
      {
        "name": "iPhone 15 128GB",
        "price": "20990000",
        "url": "https://tiki.vn/...",
        "platform": "tiki"
      }
    ],
    "lazada": [...],
    "cellphones": [...],
    "dienthoaivui": [...]
  },
  "errors": [],
  "summary": {
    "tiki": 10,
    "lazada": 8,
    "cellphones": 6,
    "dienthoaivui": 4
  }
}
```

## ⚙️ Parameters

| Parameter | Short | Description | Default | Example |
|-----------|-------|-------------|---------|---------|
| `--query` | `-q` | Search keyword (required) | - | `"iPhone 15"` |
| `--limit` | `-l` | Max products per platform | 10 | `20` |
| `--output` | `-o` | Output JSON file | Auto-generated | `"results.json"` |
| `--platforms` | - | Specific platforms only | All available | `tiki lazada` |

## 🔧 Troubleshooting

### Missing Dependencies
Nếu thiếu crawler nào đó:
```
Warning: Lazada crawler not available: No module named 'selenium'
```
→ Install: `pip install selenium webdriver-manager`

### Platform Options
- `tiki` - Nhanh nhất (API)
- `lazada` - Chậm (Selenium + browser)
- `cellphones` - Trung bình (Playwright)
- `dienthoaivui` - Trung bình (Playwright)

### Performance Tips
1. **Chạy ít platforms**: `--platforms tiki cellphones`
2. **Giảm limit**: `--limit 5`
3. **Chạy riêng lẻ** cho debug

## 📁 Output Files
- **Auto naming**: `crawl_results_20251030_103000.json`
- **Custom naming**: `--output "my_results.json"`
- **Location**: Cùng thư mục với script

## 🔄 Parallel Execution
- **Sync crawlers** (Tiki, Lazada): Chạy song song trong threads
- **Async crawlers** (Cellphones, DienThoaiVui): Chạy song song với asyncio
- **Total time** ≈ slowest crawler time (not sum of all)

## Example Commands

```bash
# Quick test với Tiki only
python run_all_crawlers.py -q "áo thun" --platforms tiki -l 5

# Full crawl cho research
python run_all_crawlers.py -q "laptop gaming" -l 50 -o "laptop_research.json"

# So sánh giá nhanh
python run_all_crawlers.py -q "iPhone 14" --platforms tiki cellphones -l 10
```