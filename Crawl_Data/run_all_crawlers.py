#!/usr/bin/env python3
"""
Run All Crawlers - Unified Product Crawler
Công cụ chạy đồng thời tất cả crawler và tổng hợp kết quả
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from datetime import datetime

# Import các crawler modules
from crawl_tiki_product import crawl_tiki_product
from lazada_crawler_complete import LazadaCrawler
from scrape_cellphones_playwright import scrape_cellphones_products
from scrape_dienthoaivui_playwright_search import scrape_dienthoaivui_products


def run_tiki_crawler(product_name: str) -> List[Dict]:
    """Chạy Tiki crawler"""
    try:
        print("Bắt đầu crawl từ Tiki...")
        return crawl_tiki_product(product_name)
    except Exception as e:
        print(f"Lỗi khi crawl từ Tiki: {e}")
        return []


def run_lazada_crawler(product_name: str) -> List[Dict]:
    """Chạy Lazada crawler"""
    try:
        print("Bắt đầu crawl từ Lazada...")
        crawler = LazadaCrawler()
        return crawler.crawl_lazada_products(product_name)
    except Exception as e:
        print(f"Lỗi khi crawl từ Lazada: {e}")
        return []


def run_cellphones_crawler(product_name: str) -> List[Dict]:
    """Chạy CellphoneS crawler"""
    try:
        print("Bắt đầu crawl từ CellphoneS...")
        return scrape_cellphones_products(product_name)
    except Exception as e:
        print(f"Lỗi khi crawl từ CellphoneS: {e}")
        return []


def run_dienthoaivui_crawler(product_name: str) -> List[Dict]:
    """Chạy Điện Thoại Vui crawler"""
    try:
        print("Bắt đầu crawl từ Điện Thoại Vui...")
        return scrape_dienthoaivui_products(product_name)
    except Exception as e:
        print(f"Lỗi khi crawl từ Điện Thoại Vui: {e}")
        return []


def run_all_crawlers_parallel(product_name: str) -> Dict:
    """
    Chạy tất cả crawler đồng thời và tổng hợp kết quả
    """
    start_time = time.time()
    
    # Danh sách các crawler functions
    crawlers = [
        ("Tiki", run_tiki_crawler),
        ("Lazada", run_lazada_crawler),
        ("CellphoneS", run_cellphones_crawler),
        ("Điện Thoại Vui", run_dienthoaivui_crawler)
    ]
    
    all_products = []
    crawler_results = {}
    
    print(f"Bắt đầu crawl sản phẩm '{product_name}' từ {len(crawlers)} trang web...")
    
    # Chạy đồng thời tất cả crawler
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit tất cả tasks
        future_to_crawler = {
            executor.submit(crawler_func, product_name): name 
            for name, crawler_func in crawlers
        }
        
        # Thu thập kết quả
        for future in as_completed(future_to_crawler):
            crawler_name = future_to_crawler[future]
            try:
                result = future.result()
                crawler_results[crawler_name] = {
                    "count": len(result),
                    "products": result
                }
                all_products.extend(result)
                print(f"Hoàn thành crawl từ {crawler_name}: {len(result)} sản phẩm")
            except Exception as e:
                print(f"Lỗi khi crawl từ {crawler_name}: {e}")
                crawler_results[crawler_name] = {
                    "count": 0,
                    "products": [],
                    "error": str(e)
                }
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Tạo báo cáo tổng hợp
    summary = {
        "search_query": product_name,
        "timestamp": datetime.now().isoformat(),
        "total_products": len(all_products),
        "execution_time_seconds": round(total_time, 2),
        "crawler_results": crawler_results,
        "products": all_products
    }
    
    print("Hoàn thành crawl tất cả trang web!")
    print(f"Tổng số sản phẩm tìm thấy: {len(all_products)}")
    print(f"Thời gian thực hiện: {total_time:.2f} giây")
    
    return summary


def save_results_to_file(results: Dict, product_name: str) -> str:
    """Lưu kết quả vào file JSON"""
    try:
        import os
        if not os.path.exists('../csv'):
            os.makedirs('../csv')
        
        timestamp = int(datetime.now().timestamp())
        filename = f"../csv/all_crawlers_{product_name.replace(' ', '_')}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Đã lưu kết quả vào file: {filename}")
        return filename
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return ""


def print_summary(results: Dict):
    """In báo cáo tóm tắt"""
    print("\n" + "="*60)
    print("           BÁO CÁO TỔNG HỢP CRAWLER")
    print("="*60)
    print(f"Từ khóa tìm kiếm: {results['search_query']}")
    print(f"Thời gian thực hiện: {results['execution_time_seconds']} giây")
    print(f"Tổng số sản phẩm: {results['total_products']}")
    print("-"*60)
    
    for crawler_name, crawler_result in results['crawler_results'].items():
        status = "✓" if crawler_result['count'] > 0 else "✗"
        error_info = f" (Lỗi: {crawler_result.get('error', 'N/A')})" if 'error' in crawler_result else ""
        print(f"{status} {crawler_name:15}: {crawler_result['count']:3} sản phẩm{error_info}")
    
    print("="*60)
    
    # Hiển thị một số sản phẩm mẫu
    if results['products']:
        print("\nMột số sản phẩm tìm thấy:")
        print("-"*60)
        for i, product in enumerate(results['products'][:5], 1):
            platform = product.get('platform', 'unknown')
            platform_display = platform.upper()
            name = product.get('name', 'N/A')[:50]
            price = product.get('price', 0)
            if price:
                price_str = f"{price:,}đ"
            else:
                price_str = "Liên hệ"
            print(f"{i}. [{platform_display}] {name} - {price_str}")
        
        if len(results['products']) > 5:
            print(f"... và {len(results['products']) - 5} sản phẩm khác")


def run_interactive():
    """Chạy chương trình với giao diện tương tác"""
    print("="*60)
    print("        CRAWLER TỔNG HỢP SẢN PHẨM")
    print("     Tiki | Lazada | CellphoneS | Điện Thoại Vui")
    print("="*60)
    
    product_name = input("Nhập tên sản phẩm cần tìm: ").strip()
    if not product_name:
        print("Tên sản phẩm không được để trống!")
        return
    
    print(f"\nĐang tìm kiếm '{product_name}' trên tất cả các trang web...")
    print("Vui lòng đợi...")
    
    try:
        # Chạy tất cả crawler
        results = run_all_crawlers_parallel(product_name)
        
        # In báo cáo
        print_summary(results)
        
        # Lưu file
        save_choice = input("\nBạn có muốn lưu kết quả vào file? (y/n): ").strip().lower()
        if save_choice in ['y', 'yes', 'có']:
            filename = save_results_to_file(results, product_name)
            if filename:
                print(f"Đã lưu kết quả vào: {filename}")
        
        return results
        
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình.")
    except Exception as e:
        print(f"Lỗi khi chạy crawler: {e}")
        print(f"Lỗi: {e}")


def crawl_all_platforms(product_name: str, limit: int = 5) -> List[Dict]:
    """
    Wrapper function để tương thích với chatbot.py
    Chạy tất cả crawler và trả về danh sách sản phẩm
    """
    try:
        results = run_all_crawlers_parallel(product_name)
        products = results.get('products', [])
        
        # Giới hạn số lượng sản phẩm nếu cần
        if limit and len(products) > limit:
            products = products[:limit]
            
        return products
    except Exception as e:
        print(f"Lỗi trong crawl_all_platforms: {e}")
        return []


def main():
    """Hàm main"""
    import sys
    
    if len(sys.argv) > 1:
        # Chạy với tham số command line
        product_name = ' '.join(sys.argv[1:])
        results = run_all_crawlers_parallel(product_name)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        # Chạy interactive mode
        run_interactive()


if __name__ == "__main__":
    main()