from typing import List, Dict
import requests
from datetime import datetime

# Tiki API configuration (copied so this module is independent)
TIKI_API_URL = "https://tiki.vn/api/v2/products"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def crawl_tiki_product(product_name: str) -> List[Dict]:
    """
    Crawl product information from Tiki API and process it directly
    Returns a list of processed products ready for vector database and analysis
    """
    params = {
        "q": product_name,
        "limit": 5,  # Increased for better coverage
        "sort": "score,price,asc",  # Sort by relevance and price
        "aggregations": 1
    }
    
    try:
        response = requests.get(TIKI_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            products = []
            current_time = datetime.now().isoformat()
            
            for idx, item in enumerate(data.get("data", []), 1):
                # Skip invalid or incomplete products
                required_fields = ["name", "price", "url_path"]
                if not all(item.get(field) for field in required_fields):
                    continue
                
                # Process price information
                current_price = item.get('price', 0)
                original_price = item.get('original_price', current_price)
                discount_rate = item.get('discount_rate', 0)
                
                # Process seller information
                seller_info = item.get("seller", {})
                seller_name = seller_info.get("name", item.get("seller_name", "Unknown Seller"))
                
                # Create unique product ID
                product_id = f"tiki_{int(datetime.now().timestamp())}_{idx}"
                
                # Build product information dictionary
                product = {
                    "id": product_id,  # Add unique ID
                    "name": item.get("name").strip(),
                    "price": current_price,
                    "original_price": original_price,
                    "discount": f"-{discount_rate}%" if discount_rate > 0 else "Không giảm giá",
                    "seller": seller_name,
                    "rating": f"{item.get('rating_average', 0):.1f}",
                    "review_count": item.get("review_count", 0),
                    "url": f"https://tiki.vn/{item.get('url_path')}",
                    "timestamp": current_time,
                    "platform": "tiki"
                }
                
                # Add badges and promotions if available
                badges = item.get("badge", {})
                if badges:
                    product["badges"] = [badge.get("text", "") for badge in badges if badge.get("text")]
                    
                # Add shipping info if available
                if item.get("shipping_text"):
                    product["shipping"] = item.get("shipping_text")
                
                products.append(product)
            
            if products:
                print(f"Tìm thấy {len(products)} sản phẩm phù hợp trên Tiki")
                return products
            else:
                print("Không tìm thấy sản phẩm nào phù hợp trên Tiki")
                return []

        print(f"Tiki API trả về mã lỗi {response.status_code}")
        return []
    except Exception as e:
        print(f"Lỗi khi crawl dữ liệu từ Tiki: {e}")
        return []
