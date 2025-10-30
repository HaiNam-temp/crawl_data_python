"""
Lazada Product Crawler - Optimized Version
Công cụ cào dữ liệu sản phẩm từ Lazada.vn (phiên bản tối ưu)
"""

import datetime
import os
import json
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from typing import List, Dict

# Simplified logging
def print_log(message):
    print(message)


class LazadaCrawler:
    """Lớp chính để crawl dữ liệu từ Lazada"""
    
    def __init__(self):
        self.base_url = "https://www.lazada.vn/catalog/?q={keyword}&page={page}"
        self.domain = "https://www.lazada.vn"
        
    def filter_keyword(self, keyword: str) -> str:
        """Lọc và format từ khóa để phù hợp với URL Lazada"""
        filtered_str = ""
        add_separator = False
        
        for i, char in enumerate(keyword):
            if 'a' <= char <= 'z' or 'A' <= char <= 'Z' or '0' <= char <= '9':
                if i > 0 and keyword[i-1] == " " and add_separator:
                    filtered_str += "-"
                filtered_str += char
                add_separator = True
                
        return filtered_str
    
    def get_timestamp(self) -> str:
        """Tạo timestamp cho tên file"""
        ct = datetime.datetime.now()
        ts = ct.timestamp()
        return str(int(ts))
    
    def create_web_driver(self, url: str) -> WebDriver:
        """Tạo Chrome WebDriver ở chế độ headless"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=chrome_options
        )
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(url)
        WebDriverWait(driver, 5)
        sleep(2)
        return driver
    
    def get_product_names(self, soup: BeautifulSoup) -> ResultSet:
        """Lấy tên sản phẩm từ HTML"""
        return soup.select('._17mcb .Bm3ON .buTCk .RfADt a')
    
    def get_price_items(self, soup: BeautifulSoup) -> ResultSet:
        """Lấy giá sản phẩm từ HTML"""
        return soup.select('._17mcb .Bm3ON .buTCk .aBrP0 .ooOxS')
    
    def get_historical_sold(self, soup: BeautifulSoup) -> ResultSet:
        """Lấy thông tin số lượng đã bán từ HTML"""
        return soup.select('._17mcb .Bm3ON .buTCk ._6uN7R')
    
    def get_product_origin(self, soup: BeautifulSoup) -> ResultSet:
        """Lấy thông tin xuất xứ sản phẩm từ HTML"""
        return soup.select('._17mcb .Bm3ON .buTCk ._6uN7R .oa6ri')
    
    def get_product_ratings(self, soup: BeautifulSoup) -> ResultSet:
        """Lấy thông tin rating từ HTML"""
        return soup.select('._17mcb .Bm3ON .buTCk .qzqFw')
    
    def get_review_counts(self, soup: BeautifulSoup) -> ResultSet:
        """Lấy thông tin số lượng đánh giá từ HTML"""
        return soup.select('._17mcb .Bm3ON .buTCk .qzqFw ._1cEkb')
    
    def get_sold_item_at_index(self, index: int, sold_items: ResultSet) -> str:
        """Lấy số lượng đã bán tại index cụ thể"""
        try:
            sold_item = sold_items[index].select('._1cEkb')
            return sold_item[0].text.strip() if sold_item else "0"
        except (IndexError, AttributeError):
            return "0"
    
    def get_rating_at_index(self, index: int, rating_items: ResultSet) -> float:
        """Lấy rating tại index cụ thể"""
        try:
            # Tìm element chứa rating
            if index < len(rating_items):
                rating_element = rating_items[index]
                # Tìm các pattern rating phổ biến
                rating_selectors = ['.review-score', '._9-ogB', '.rating-average', '[data-rating]']
                for selector in rating_selectors:
                    rating_node = rating_element.select(selector)
                    if rating_node:
                        rating_text = rating_node[0].text.strip()
                        import re
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            return float(rating_match.group(1))
                
                # Fallback: tìm số trong toàn bộ text của element
                full_text = rating_element.get_text()
                import re
                rating_matches = re.findall(r'(\d+\.?\d*)\s*/?\s*5|(\d+\.?\d*)\s*sao', full_text)
                if rating_matches:
                    for match in rating_matches:
                        for group in match:
                            if group:
                                rating_val = float(group)
                                if 0 <= rating_val <= 5:
                                    return rating_val
            return 0.0
        except (IndexError, AttributeError, ValueError):
            return 0.0
    
    def get_review_count_at_index(self, index: int, review_items: ResultSet) -> int:
        """Lấy số lượng đánh giá tại index cụ thể"""
        try:
            if index < len(review_items):
                review_element = review_items[index]
                review_text = review_element.get_text()
                import re
                # Tìm pattern số đánh giá
                review_matches = re.findall(r'(\d+)\s*(?:đánh giá|review|nhận xét)', review_text, re.IGNORECASE)
                if review_matches:
                    return int(review_matches[0])
                
                # Fallback: tìm số trong parentheses
                paren_matches = re.findall(r'\((\d+)\)', review_text)
                if paren_matches:
                    return int(paren_matches[0])
            return 0
        except (IndexError, AttributeError, ValueError):
            return 0
    
    def get_product_info_json(self, soup: BeautifulSoup):
        """Trích xuất thông tin sản phẩm và trả về list dict với format giống crawl_tiki_product"""
        name_items = self.get_product_names(soup)
        price_items = self.get_price_items(soup)
        sold_items = self.get_historical_sold(soup)
        product_origin = self.get_product_origin(soup)
        rating_items = self.get_product_ratings(soup)
        review_items = self.get_review_counts(soup)
        
        products = []
        current_time = datetime.datetime.now().isoformat()
        
        for index in range(len(name_items)):
            try:
                name = name_items[index].get('title', '').strip()
                if not name:
                    continue
                
                # Xử lý giá
                price_text = price_items[index].text.strip() if index < len(price_items) else "0"
                # Trích xuất số từ text giá (loại bỏ ký tự không phải số)
                import re
                price_numbers = re.findall(r'[\d,\.]+', price_text.replace('₫', '').replace('đ', ''))
                current_price = 0
                if price_numbers:
                    try:
                        # Lấy số đầu tiên, loại bỏ dấu phẩy/chấm
                        price_str = price_numbers[0].replace(',', '').replace('.', '')
                        current_price = int(price_str)
                    except (ValueError, IndexError):
                        current_price = 0
                
                sold = self.get_sold_item_at_index(index, sold_items)
                origin = product_origin[index].text.strip() if index < len(product_origin) else "Unknown Seller"
                
                # Lấy rating và review count
                rating = self.get_rating_at_index(index, rating_items)
                review_count = self.get_review_count_at_index(index, review_items)
                
                # Lấy link sản phẩm
                link = name_items[index].get('href', '').strip()
                if link:
                    if link.startswith('/'):
                        link = self.domain + link
                    elif link.startswith('//'):
                        link = 'https:' + link
                else:
                    link = 'N/A'
                
                # Tạo unique product ID
                product_id = f"lazada_{int(datetime.datetime.now().timestamp())}_{index}"
                
                # Tạo product dict với format giống crawl_tiki_product
                product = {
                    "id": product_id,
                    "name": name,
                    "price": current_price,
                    "original_price": current_price,  # Lazada không có giá gốc rõ ràng
                    "discount": "Không giảm giá",  # Có thể cập nhật sau nếu có thông tin
                    "seller": origin,
                    "rating": f"{rating:.1f}",
                    "review_count": review_count,
                    "url": link,
                    "timestamp": current_time,
                    "platform": "lazada",
                    "sold_count": sold
                }
                products.append(product)
                
            except (IndexError, AttributeError) as e:
                print(f"Error processing product {index}: {e}")
                continue
        
        return products

    def get_product_info(self, soup: BeautifulSoup):
        """Trích xuất toàn bộ thông tin sản phẩm (CSV format - legacy)"""
        name_items = self.get_product_names(soup)
        price_items = self.get_price_items(soup)
        sold_items = self.get_historical_sold(soup)
        product_origin = self.get_product_origin(soup)
        
        for index in range(len(name_items)):
            try:
                name = name_items[index].get('title', '').strip()
                price = price_items[index].text.strip()
                sold = self.get_sold_item_at_index(index, sold_items)
                origin = product_origin[index].text.strip() if index < len(product_origin) else "N/A"
                
                # Lấy link sản phẩm
                link = name_items[index].get('href', '').strip()
                if link:
                    if link.startswith('/'):
                        link = self.domain + link
                    elif link.startswith('//'):
                        link = 'https:' + link
                else:
                    link = 'N/A'
                
                product_info = f"{name} | {price} | {sold} | {origin} | {link}\n"
                yield product_info
                
            except (AttributeError, IndexError):
                continue
    
    def crawl_lazada_products(self, product_name: str) -> List[Dict]:
        """
        Crawl sản phẩm từ Lazada và trả về list dict với format giống crawl_tiki_product
        Giới hạn chỉ lấy 5 sản phẩm
        """
        try:
            filtered_keyword = self.filter_keyword(product_name)
            all_products = []
            
            for page in range(1, 3):  # Crawl tối đa 2 trang
                url = self.base_url.format(keyword=filtered_keyword, page=page)
                
                driver = self.create_web_driver(url)
                html = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
                soup = BeautifulSoup(html, "html.parser")
                
                products = self.get_product_info_json(soup)
                
                # Thêm từng sản phẩm và kiểm tra giới hạn
                for product in products:
                    if len(all_products) >= 5:  # Giới hạn 5 sản phẩm
                        break
                    all_products.append(product)
                
                driver.quit()
                
                # Nếu đã đủ 5 sản phẩm thì dừng
                if len(all_products) >= 5:
                    break
                
                if page < 2:
                    sleep(2)
            
            # Đảm bảo chỉ trả về tối đa 5 sản phẩm
            all_products = all_products[:5]
            
            if all_products:
                print(f"Tìm thấy {len(all_products)} sản phẩm từ Lazada")
            else:
                print("Không tìm thấy sản phẩm nào từ Lazada")
            
            return all_products
        
        except Exception as e:
            print(f"Lỗi khi crawl dữ liệu từ Lazada: {e}")
            return []

    def crawl_products(self, keyword: str) -> str:
        """Crawl sản phẩm từ trang 1 đến 2"""
        if not os.path.exists('csv'):
            os.makedirs('csv')
            
        timestamp = self.get_timestamp()
        filename = f"csv/lazada_{keyword.replace(' ', '_')}_pages_1_to_2_{timestamp}.csv"
        
        total_products = 0
        
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write("Tên sản phẩm | Giá | Đã bán | Xuất xứ | Link sản phẩm\n")
            f.write("-" * 100 + "\n")
            
            for page in range(1, 3):  # Cố định 2 trang
                filtered_keyword = self.filter_keyword(keyword)
                url = self.base_url.format(keyword=filtered_keyword, page=page)
                
                driver = self.create_web_driver(url)
                html = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
                soup = BeautifulSoup(html, "html.parser")
                
                products = self.get_product_info(soup)
                
                for product in products:
                    f.write(product)
                    total_products += 1
                
                driver.quit()
                
                if page < 2:
                    sleep(2)
        
        return filename
    
    def run_interactive(self):
        """Chạy chương trình với giao diện đơn giản"""
        print("Lazada Product Crawler")
        print("-" * 30)
        
        keyword = input("Nhập tên sản phẩm: ").strip()
        if not keyword:
            print("Tên sản phẩm không được để trống!")
            return
        
        try:
            result_file = self.crawl_products(keyword)
            print(f"Hoàn thành! File: {result_file}")
                
        except Exception as e:
            print(f"Lỗi: {e}")


def main():
    """Hàm main để chạy chương trình"""
    crawler = LazadaCrawler()
    crawler.run_interactive()


if __name__ == "__main__":       
    main()