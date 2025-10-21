from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain.embeddings import OpenAIEmbeddings
from operator import itemgetter
import json
from typing import List, Dict
import requests
import re
from datetime import datetime
import dotenv
import os
dotenv.load_dotenv()
# Initialize ChatOpenAI
chat_model = ChatOpenAI(
    model="gpt-5",
    temperature=0
)

# Initialize vector database for product data
PRODUCTS_CHROMA_PATH = "chroma_data/"

# Initialize embeddings with explicit API key
embedding_function = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-ada-002"
)

# Initialize vector database
products_vector_db = Chroma(
    persist_directory=PRODUCTS_CHROMA_PATH,
    embedding_function=embedding_function
)
products_retriever = products_vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Tiki API configuration
TIKI_API_URL = "https://tiki.vn/api/v2/products"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def create_chain_with_template(system_template: str, human_template: str = "{question}"):
    """Helper function to create a chain with given templates"""
    # Create base prompts
    system_message_prompt = SystemMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["context"],
            template=system_template
        )
    )
    
    human_message_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=["question"],
            template=human_template
        )
    )
    
    chat_prompt = ChatPromptTemplate(
        messages=[system_message_prompt, human_message_prompt]
    )

    # For product search (using vector retriever)
    if "Tôi sẽ tìm kiếm" in system_template:
        return (
            {
                "context": itemgetter("question") | products_retriever,
                "question": itemgetter("question"),
            }
            | chat_prompt
            | chat_model
            | StrOutputParser()
        )
    
    # For price comparison (using direct context)
    else:
        from langchain.chains import LLMChain
        
        chain = LLMChain(
            llm=chat_model,
            prompt=chat_prompt,
            verbose=False
        )
        
        def process_chain(inputs: dict) -> str:
            try:
                result = chain.invoke(inputs)
                return result["text"] if isinstance(result, dict) else str(result)
            except Exception as e:
                raise ValueError(f"Error processing chain: {str(e)}")
        
        return process_chain

# Function to crawl product data from Tiki
def crawl_tiki_product(product_name: str) -> List[Dict]:
    """
    Crawl product information from Tiki API and process it directly
    Returns a list of processed products ready for vector database and analysis
    """
    params = {
        "q": product_name,
        "limit": 20,  # Increased for better coverage
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
                    "price_display": f"{current_price:,.0f} VNĐ",
                    "original_price_display": f"{original_price:,.0f} VNĐ",
                    "discount": f"-{discount_rate}%" if discount_rate > 0 else "Không giảm giá",
                    "seller": seller_name,
                    "rating": f"{item.get('rating_average', 0):.1f}",
                    "review_count": item.get("review_count", 0),
                    "stock_status": item.get("inventory_status", "Unknown").capitalize(),
                    "url": f"https://tiki.vn/{item.get('url_path')}",
                    "thumbnail": item.get("thumbnail_url", ""),
                    "platform": "Tiki",
                    "category": item.get("category", {}).get("name", "Unknown"),
                    "brand": item.get("brand", {}).get("name", "Unknown Brand"),
                    "timestamp": current_time
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
                print(f"\nTìm thấy {len(products)} sản phẩm phù hợp trên Tiki:")
                return products
            else:
                print("\nKhông tìm thấy sản phẩm nào phù hợp trên Tiki")
                return []
                
        print(f"\nLỗi: Tiki API trả về mã lỗi {response.status_code}")
        return []
    except Exception as e:
        print(f"\nLỗi khi crawl dữ liệu từ Tiki: {str(e)}")
        return []

product_search_template = """
Bạn là trợ lý mua sắm thông minh Sophie, nhiệm vụ của bạn là giúp người dùng tìm kiếm và so sánh giá sản phẩm trên các sàn thương mại điện tử.

Hãy trả lời một cách thân thiện và tự nhiên, sử dụng ngôn ngữ dễ hiểu. Với mỗi sản phẩm được đề cập, LUÔN LUÔN cung cấp đường link trực tiếp để người dùng có thể mua hàng.

LUÔN LUÔN phân tích các thông tin sau cho mỗi sản phẩm:
1. Tên sản phẩm đầy đủ
2. Giá hiện tại: [Giá] VNĐ
3. Giá gốc (nếu có): [Giá gốc] VNĐ
4. Phần trăm giảm giá (nếu có): -[X]%
5. Người bán: [Tên người bán]
6. Đánh giá: [X] sao ([Số lượng] đánh giá)
7. Link sản phẩm: [URL]

Sau khi liệt kê thông tin, hãy:
1. So sánh giá giữa các sản phẩm
2. Phân tích ưu/nhược điểm của mỗi lựa chọn
3. Đề xuất lựa chọn tốt nhất dựa trên:
   - Mức giá hợp lý
   - Độ uy tín của người bán
   - Đánh giá từ người mua
   - Chính sách bảo hành/đổi trả
4. Đưa ra lời khuyên về thời điểm mua sắm phù hợp

Nếu sản phẩm không có trong dữ liệu, hãy nói: "Tôi sẽ tìm kiếm sản phẩm này trên Tiki cho bạn."

Bối cảnh hiện có:
{context}
"""

product_search_chain = create_chain_with_template(product_search_template)

# Price Comparison Chain
price_comparison_template = """
Bạn là Sophie - chuyên gia phân tích giá cả thông minh. Bạn sẽ phân tích thông tin của các sản phẩm trong context được cung cấp.
Dữ liệu sản phẩm được cung cấp dưới dạng JSON, với các trường thông tin như: name (tên sản phẩm), price (giá), original_price (giá gốc), 
discount (giảm giá), seller (người bán), rating (đánh giá), review_count (số lượng đánh giá), url (link sản phẩm).

LUÔN LUÔN phân tích chi tiết theo định dạng sau:

💰 PHÂN TÍCH GIÁ:
1. So sánh giá từ thấp đến cao:
   - [Tên SP 1]: [Giá hiện tại] (Giá gốc: [Giá gốc] | Giảm: [Phần trăm]%)
   - [Tên SP 2]: [Giá hiện tại] (Giá gốc: [Giá gốc] | Giảm: [Phần trăm]%)
   ...

2. Phân tích khuyến mãi:
   - Sản phẩm có mức giảm giá tốt nhất: [Tên SP] ([Phần trăm giảm]%)
   - Số tiền tiết kiệm được: [Số tiền] VNĐ
   
👨‍🏫 ĐÁNH GIÁ NGƯỜI BÁN:
- Người bán uy tín nhất: [Tên người bán]
  + Đánh giá trung bình: [X] sao
  + Số lượng đánh giá: [Số lượng]
  + Link sản phẩm: [URL]

🎯 ĐỀ XUẤT MUA SẮM:
1. Lựa chọn tốt nhất: [Tên SP]
   Giá: [Giá] VNĐ
   Người bán: [Tên người bán]
   Đánh giá: [X] sao ([Số lượng] đánh giá)
   Link: [URL]
   Lý do chọn:
   + [Lý do 1]
   + [Lý do 2]

2. Lựa chọn thay thế: [Tên SP]
   Giá: [Giá] VNĐ
   Người bán: [Tên người bán]
   Đánh giá: [X] sao ([Số lượng] đánh giá)
   Link: [URL]
   Lý do chọn:
   + [Lý do 1]
   + [Lý do 2]

💡 LỜI KHUYÊN:
1. Thời điểm mua sắm: [Đề xuất dựa trên xu hướng giá và khuyến mãi]
2. Các lưu ý:
   - [Lưu ý về giá cả]
   - [Lưu ý về người bán]
   - [Lưu ý về bảo hành/đổi trả]

Bối cảnh hiện có:
{context}
"""

price_comparison_chain = create_chain_with_template(price_comparison_template)
