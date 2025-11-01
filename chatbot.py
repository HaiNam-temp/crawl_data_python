from dotenv import load_dotenv
from logger_config import get_logger
from tool import (
    product_search_chain,
    price_comparison_chain,
    get_vector_db,
    get_chat_model
)
# Import multi-platform crawler thay cho Tiki only
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Crawl_Data'))
from Crawl_Data.run_all_crawlers import crawl_all_platforms

import json
from datetime import datetime
from langchain_core.documents import Document
load_dotenv()
logger = get_logger(__name__)
products_vector_db = get_vector_db()
chat_model = get_chat_model()
from backend.database import save_products
def process_user_query(user_query: str) -> str:
    logger.info(f"User query: {user_query}")
    try:
        intent_prompt = f"""
        Bạn là một trợ lý AI. Hãy phân loại câu sau thành một trong hai loại:
        1. "chat" - nếu người dùng chỉ đang trò chuyện, hỏi linh tinh, không yêu cầu so sánh giá.
        2. "compare" - nếu người dùng đang muốn tìm, xem, hoặc so sánh giá sản phẩm.

        Câu người dùng: "{user_query}"

        Nếu là "chat", chỉ trả về từ "chat".
        Nếu là "compare", hãy trả về **tên sản phẩm kèm đặc điểm** (ví dụ: "iPhone 14 Pro 128GB").
        """

        intent_result = chat_model.invoke(intent_prompt).content.strip()
        logger.info(f"Detected intent result: {intent_result}")

        # 🧩 Bước 2: Xử lý intent
        if intent_result.lower() == "chat":
            response = chat_model.invoke(
                f"Người dùng nói: {user_query}. Hãy phản hồi tự nhiên, thân thiện như một trợ lý AI."
            ).content
            return response

        # Nếu không phải chat, coi kết quả là tên sản phẩm cần tìm
        product_name = intent_result
        logger.info(f"Extracted product name: {product_name}")

        # 🔍 Bước 3: Tìm sản phẩm
        # product_search_chain may be either a chain-like object with an
        # .invoke(...) method or a plain callable (fallback function). Handle
        # both cases to avoid AttributeError when a simple function was
        # returned during initialization.
        def _call_chain(chain, inputs):
            try:
                if hasattr(chain, 'invoke') and callable(getattr(chain, 'invoke')):
                    return chain.invoke(inputs)
                elif callable(chain):
                    return chain(inputs)
                else:
                    raise ValueError('Provided chain is not callable')
            except Exception as e:
                logger.error('Error invoking chain: %s', e, exc_info=True)
                raise

        search_result = _call_chain(product_search_chain, {"question": product_name})
        # If no relevant results found in vector database, crawl from all platforms
        if "tôi sẽ tìm kiếm" in search_result.lower():
            logger.info(f"Search result: {search_result}")
            # Crawl từ tất cả platforms thay vì chỉ Tiki
            all_products = crawl_all_platforms(product_name, limit=None)

            # Persist crawled products to SQL database for long-term storage
            try:
                saved_count = save_products(all_products)
                logger.info(f"Persisted {saved_count} products into SQL DB after crawling.")
            except Exception as e:
                logger.error(f"Error saving crawled products to SQL DB: {e}")

            if all_products:
                # Start price comparison immediately with crawled data
                context_data = json.dumps(all_products, ensure_ascii=False)
                try:
                    comparison_result = _call_chain(price_comparison_chain, {
                        "context": context_data,
                        "question": f"So sánh giá {product_name} từ các kết quả vừa tìm được"
                    })
                    if not comparison_result:
                        comparison_result = "Xin lỗi, không thể phân tích giá sản phẩm lúc này."
                except Exception as e:
                    logger.error(f"Error during price comparison: {str(e)}")
                    comparison_result = "Xin lỗi, có lỗi xảy ra khi phân tích giá sản phẩm."
                
                # Add new products to vector database
                try:
                    # Convert products to Document objects
                    documents = []
                    for product in all_products:
                        # Convert product dict to string for embedding
                        product_text = json.dumps(product, ensure_ascii=False)
                        
                        # Create Document object with metadata
                        doc = Document(
                            page_content=product_text,
                            metadata={
                                "name": product["name"],
                                "price": product["price"],
                                "url": product["url"],
                                "rating": product["rating"],
                                "review_count": product["review_count"],
                                "timestamp": product["timestamp"]
                            }
                        )
                        documents.append(doc)

                    
                    # Add documents to vector store
                    products_vector_db.add_documents(documents)
                    logger.info("Updated vector database with new products.")
                except Exception as e:
                    logger.error(f"Error updating vector database: {str(e)}")
                    logger.warning("Search data was processed but may not be stored.")

                return comparison_result
            else:
                return "Xin lỗi, tôi không tìm thấy thông tin về sản phẩm này trên các sàn thương mại điện tử. Vui lòng thử lại với từ khóa khác."
        
        return search_result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."

def chat_loop():
    """Main chat loop"""
    print("="*50)
    print("Chào mừng bạn đến với Sophie - Trợ lý so sánh giá thông minh!")
    print("Tôi có thể giúp bạn:")
    print("1. Tìm kiếm thông tin sản phẩm")
    print("2. So sánh giá giữa các sản phẩm")
    print("3. Phân tích và đưa ra đề xuất mua sắm")
    print("\nĐể thoát, bạn có thể gõ 'quit' hoặc 'exit'")
    print("="*50)
    
    while True:
        try:
            user_input = input("\nBạn muốn tìm sản phẩm gì? ").strip()
            
            # Skip empty input or input starting with &
            if not user_input or user_input.startswith('&'):
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\nCảm ơn bạn đã sử dụng dịch vụ. Hẹn gặp lại!")
                break
                
            response = process_user_query(user_input)
            print(f"\nSophie: {response}")
            
        except EOFError:
            # Handle Ctrl+D or similar input termination
            print("\nKết thúc chương trình do ngắt input.")
            break
        except KeyboardInterrupt:
            # Handle Ctrl+C
            print("\nKết thúc chương trình theo yêu cầu người dùng.")
            break
        except Exception as e:
            print(f"\nCó lỗi xảy ra: {str(e)}")
            print("Vui lòng thử lại.")

if __name__ == "__main__":
    chat_loop()