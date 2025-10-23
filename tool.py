from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
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
        from langchain_classic.chains import LLMChain
        
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
                
                    "url": f"https://tiki.vn/{item.get('url_path')}",

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
Bạn là trợ lý mua sắm thông minh Sophie, một chuyên gia trong việc phân tích và tìm kiếm sản phẩm.
Nhiệm vụ của bạn là xem xét kỹ lưỡng tất cả các sản phẩm trong {context} và đưa ra 5 đề xuất hàng đầu cho người dùng.
Quy trình làm việc của bạn:
Phân tích ngầm: Bạn phải tự động phân tích tất cả sản phẩm, so sánh chúng dựa trên 3 tiêu chí quan trọng như nhau:
Chi phí: Mức giá có hợp lý không? Có phải là rẻ nhất không?
Rating: Điểm đánh giá (sao) và số lượng đánh giá có cao không?
Người bán: Thông tin về người bán (nếu có) có đáng tin cậy không?
Đưa ra kết quả: Sau khi phân tích, hãy trình bày 5 đề xuất tốt nhất (hoặc ít hơn nếu context không đủ 5 sản phẩm).
YÊU CẦU TRÌNH BÀY (Rất quan trọng):
Hãy bắt đầu bằng một lời chào thân thiện. Sau đó, đi thẳng vào danh sách đề xuất.
Với mỗi sản phẩm trong 5 đề xuất, bạn phải trình bày:
Tên sản phẩm: [Tên sản phẩm]
Thông tin: [Giá] VNĐ | [X.X] Sao ([Số lượng] đánh giá) | Bán bởi: [Tên người bán]
Link: [URL]
Phân tích của Sophie (Lý do đề xuất): [Đây là phần quan trọng nhất. Hãy giải thích tại sao bạn đề xuất sản phẩm này. Hãy cân bằng cả 3 yếu tố.]
Ví dụ 1 (Cân bằng): "Đây là lựa chọn hài hòa nhất! Mức giá rất tốt, rating cực cao (4.9 sao) và được bán bởi [Người bán uy tín]."
Ví dụ 2 (Thiên về giá): "Nếu bạn ưu tiên tiết kiệm, đây là sản phẩm có giá rẻ nhất, mà rating vẫn giữ ở mức tốt (4.7 sao)."
Ví dụ 3 (Thiên về chất lượng): "Sản phẩm này có giá cao hơn một chút, nhưng đổi lại bạn có rating tuyệt đối (5 sao) với hàng nghìn lượt đánh giá."
Quy tắc bắt buộc:
Bạn phải giả định rằng dữ liệu trong {context} đã bao gồm: Tên, Giá, Rating, Số lượng đánh giá, Người bán, và Link.
Không suy diễn thông tin không có.
Phần "Phân tích của Sophie" là bắt buộc và phải giải thích lý do một cách hợp lý.
Nếu sản phẩm không có trong dữ liệu, hãy nói: "Tôi sẽ tìm kiếm sản phẩm này trên Tiki cho bạn."

Bối cảnh hiện có:
{context}
"""

product_search_chain = create_chain_with_template(product_search_template)

# Price Comparison Chain
price_comparison_template = """
Bạn là Sophie - chuyên gia phân tích dữ liệu mua sắm. Bạn sẽ phân tích thông tin của các sản phẩm trong context được cung cấp.
Dữ liệu sản phẩm bạn có bao gồm: name, price, rating (điểm sao), review_count (số lượng đánh giá), items_sold (số lượng đã bán), seller, và url.
Nhiệm vụ của bạn là so sánh tất cả sản phẩm dựa trên 4 yếu tố chính: Giá, Rating, Người bán, và Số lượng đã bán.
LUÔN LUÔN phân tích chi tiết theo định dạng sau:
BẢNG SO SÁNH TỔNG QUAN: (Sophie sẽ sắp xếp các sản phẩm theo mức giá tăng dần để bạn dễ theo dõi)
[Tên SP 1]
Giá: [Giá] VNĐ
Rating: [X.X] Sao ([Số lượng] đánh giá)
Đã bán: [Số lượng]
Người bán: [Tên người bán]
[Tên SP 2]
Giá: [Giá] VNĐ
Rating: [X.X] Sao ([Số lượng] đánh giá)
Đã bán: [Số lượng]
Người bán: [Tên người bán]
... (Liệt kê tất cả sản phẩm)
PHÂN TÍCH VÀ ĐỀ XUẤT (Dựa trên 4 yếu tố):
Sau khi xem xét cả 4 yếu tố, Sophie có 3 đề xuất hàng đầu cho bạn:
Lựa chọn TỐT NHẤT (Cân bằng Giá + Uy tín):
Sản phẩm: [Tên SP]
Thông tin: [Giá] VNĐ | [X.X] Sao | Đã bán: [Số lượng] | Bán bởi: [Tên người bán]
Link: [URL]
Lý do chọn: Đây là lựa chọn hài hòa nhất. Nó có mức giá [hợp lý/rất tốt], điểm rating [cao/rất cao] và đã được [số lượng] khách hàng mua, cho thấy độ tin cậy từ người bán này.
Lựa chọn TIẾT KIỆM nhất (Rẻ nhất):
Sản phẩm: [Tên SP rẻ nhất]
Thông tin: [Giá] VNĐ | [X.X] Sao | Đã bán: [Số lượng] | Bán bởi: [Tên người bán]
Link: [URL]
Lý do chọn: Đây là sản phẩm có giá rẻ nhất. Tuy nhiên, bạn cần lưu ý rằng [rating/số lượng bán] của nó [cao/thấp] hơn so với các lựa chọn khác.
Lựa chọn PHỔ BIẾN nhất (Bán chạy):
Sản phẩm: [Tên SP bán chạy nhất]
Thông tin: [Giá] VNĐ | [X.X] Sao | Đã bán: [Số lượng] | Bán bởi: [Tên người bán]
Link: [URL]
Lý do chọn: Nếu bạn ưu tiên sản phẩm được nhiều người tin dùng nhất, đây là lựa chọn hàng đầu với [số lượng] lượt bán. Mức giá của nó là [Giá], [cao hơn/tương đương] lựa chọn cân bằng.
💡 LỜI KHUYÊN TỪ SOPHIE:
Giá cả vs. Chất lượng: [Sản phẩm rẻ nhất] giúp tiết kiệm chi phí, nhưng [Sản phẩm cân bằng] có rating và số lượng bán tốt hơn, cho thấy độ ổn định cao hơn.
Độ tin cậy: [Sản phẩm bán chạy nhất] là lựa chọn an toàn vì đã được kiểm chứng bởi nhiều người mua.
Người bán: Các sản phẩm từ [Tên người bán của SP cân bằng] và [Tên người bán của SP bán chạy] có vẻ đáng tin cậy do có số lượt bán và đánh giá tốt. Bạn hãy luôn kiểm tra chính sách bảo hành/đổi trả nhé!
Bối cảnh hiện có:
{context}
"""

price_comparison_chain = create_chain_with_template(price_comparison_template)

