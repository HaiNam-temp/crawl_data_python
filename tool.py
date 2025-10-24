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
from logger_config import get_logger
logger = get_logger(__name__)
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

# import split functions from their new modules
from create_chain_with_template import create_chain_with_template
from Crawl_Data.crawl_tiki_product import crawl_tiki_product

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

# Replace the direct chain with a function that first crawls Tiki for fresh data,
# then feeds that data into the LLM chain for analysis.
def product_search_chain(inputs: dict) -> str:
    """Given inputs with 'question', crawl Tiki for product data and run the
    product search LLM on the crawled data. Returns the LLM text result.
    """
    question = (inputs or {}).get("question", "")
    logger.info("product_search_chain called with question=%r", question)

    # Crawl Tiki for the query
    try:
        crawled = crawl_tiki_product(question)
    except Exception as e:
        return f"[ERROR] Lỗi khi crawl dữ liệu: {e}"

    if not crawled:
        # If nothing found, return an explicit message so callers can decide to
        # fallback to other behavior if desired.
        return "Tôi sẽ tìm kiếm sản phẩm này trên Tiki cho bạn."

    # Build context from crawled products and run the LLM chain.
    context_data = json.dumps(crawled, ensure_ascii=False)

    # The product_search_template contains the heuristic phrase that would make
    # create_chain_with_template return a retriever-based chain. To force the
    # LLM-only branch, create a sanitized template without that line.
    sanitized_template = product_search_template.replace(
        'Nếu sản phẩm không có trong dữ liệu, hãy nói: "Tôi sẽ tìm kiếm sản phẩm này trên Tiki cho bạn."',
        ""
    )

    # Add a persona definition (tính cách) similar to the price_comparison_template
    # so the LLM receives an explicit role and tone instruction when processing data.
    persona_definition = (
        "Bạn là Sophie - trợ lý mua sắm thông minh và chuyên gia phân tích dữ liệu mua sắm. "
        "Bạn cung cấp phân tích rõ ràng, khách quan, và thân thiện; luôn nêu lý do cho mỗi đề xuất và so sánh."
    )

    final_template = persona_definition + "\n\n" + sanitized_template

    llm_processor = create_chain_with_template(final_template)

    # llm_processor should be a callable that accepts a dict with 'context' and 'question'
    try:
        result = llm_processor({"context": context_data, "question": question})
        return result
    except Exception as e:
        # Try alternate invocation style if the chain exposes an invoke method
        try:
            return llm_processor.invoke({"context": context_data, "question": question})
        except Exception as ex:
            return f"[ERROR] Lỗi khi gọi LLM chain: {ex}"

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

