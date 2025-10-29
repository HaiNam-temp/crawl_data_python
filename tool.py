from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_classic.callbacks.base import BaseCallbackHandler

from operator import itemgetter
import json
from typing import List, Dict
import requests
import re
from datetime import datetime
import dotenv
import os
dotenv.load_dotenv()
from logger_config import get_logger
logger = get_logger(__name__)
# Initialize ChatOpenAI

# Initialize vector database for product data
PRODUCTS_CHROMA_PATH = "chroma_data/"

# Initialize embeddings with explicit API key
_vector_db = None
_embeddings = None
_chat_model = None

class StreamingCallbackHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs):
        """In ra từng token khi model stream"""
        print(token, end="", flush=True)
# Initialize vector database
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-ada-002"
        )
    return _embeddings

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        embeddings = get_embeddings()
        _vector_db = Chroma(
            persist_directory=PRODUCTS_CHROMA_PATH,
            embedding_function=embeddings
        )
    return _vector_db

def get_chat_model():
    global _chat_model
    if _chat_model is None:
        _chat_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            streaming=True,
            callbacks=[StreamingCallbackHandler()]
        )
    return _chat_model
# import split functions from their new modules
from create_chain_with_template import create_chain_with_template
from Crawl_Data.crawl_tiki_product import crawl_tiki_product

product_search_template = """
Bạn là Sophie, trợ lý mua sắm chuyên phân tích sản phẩm.
Nhiệm vụ: Xem xét {context}, phân tích ngầm (Giá, Rating, Người bán) và đề xuất 5 sản phẩm hàng đầu.

Yêu cầu trình bày:
1. Chào thân thiện, sau đó liệt kê ngay 5 đề xuất (hoặc ít hơn nếu context không đủ).
2. Định dạng cho mỗi sản phẩm:
   Tên sản phẩm: [Tên sản phẩm]
   Thông tin: [Giá] VNĐ | [X.X] Sao ([Số lượng] đánh giá) | Bán bởi: [Tên người bán]
   Link: [URL]
   Phân tích của Sophie: [**Bắt buộc:** Giải thích ngắn gọn lý do đề xuất, cân bằng 3 yếu tố. Ví dụ: "Lựa chọn hài hòa giá tốt, rating cao" hoặc "Rẻ nhất nhưng rating vẫn tốt" hoặc "Đắt hơn nhưng rating tuyệt đối"].
Quy tắc:
- Luôn giả định {context} có đủ dữ liệu (Tên, Giá, Rating, Lượt, Người bán, Link).
- Phần "Phân tích của Sophie" là bắt buộc và phải hợp lý.
Phân tích của Sophie (Lý do đề xuất): [Đây là phần quan trọng nhất. Hãy giải thích tại sao bạn đề xuất sản phẩm này. Hãy cân bằng cả 3 yếu tố.]
Ví dụ 1 (Cân bằng): "Đây là lựa chọn hài hòa nhất! Mức giá rất tốt, rating cực cao (4.9 sao) và được bán bởi [Người bán uy tín]."
Ví dụ 2 (Thiên về giá): "Nếu bạn ưu tiên tiết kiệm, đây là sản phẩm có giá rẻ nhất, mà rating vẫn giữ ở mức tốt (4.7 sao)."
Ví dụ 3 (Thiên về chất lượng): "Sản phẩm này có giá cao hơn một chút, nhưng đổi lại bạn có rating tuyệt đối (5 sao) với hàng nghìn lượt đánh giá."
- Nếu {context} không có sản phẩm nào, hãy nói: "Tôi sẽ tìm kiếm sản phẩm này trên Tiki cho bạn."
Bối cảnh hiện có:
{context}
"""

product_search_chain = create_chain_with_template(product_search_template)
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
Sản phẩm: 
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

