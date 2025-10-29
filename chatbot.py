from dotenv import load_dotenv
from logger_config import get_logger
from tool import (
    product_search_chain,
    price_comparison_chain,
    crawl_tiki_product,
    get_vector_db,
    get_chat_model
)
import os
import json
from datetime import datetime
from langchain_core.documents import Document
load_dotenv()
logger = get_logger(__name__)
products_vector_db = get_vector_db()
chat_model = get_chat_model()
def process_user_query(user_query: str) -> str:
    logger.info(f"User query: {user_query}")
    try:
        # Extract product name from query using basic text cleaning
        intent_prompt = f"""
        Bạn là một trợ lý AI. Hãy phân loại câu sau thành một trong hai loại:
        1. "chat" - nếu người dùng chỉ đang trò chuyện, hỏi linh tinh, không yêu cầu so sánh giá.
        2. "compare" - nếu người dùng đang muốn tìm, xem, hoặc so sánh giá sản phẩm.

        Câu người dùng: "{user_query}"

        Chỉ trả về đúng một từ: chat hoặc compare.
        """

        intent = chat_model.invoke(intent_prompt).content.strip().lower()
        logger.info(f"Detected intent: {intent}")

        if intent == "chat":
            # 💬 Trả lời như trợ lý trò chuyện
            response = chat_model.invoke(f"Người dùng nói: {user_query}. Hãy phản hồi tự nhiên, thân thiện.").content
            return response
        
        product_name = user_query.lower()
        for term in ["tìm", "giá", "sản phẩm", "thông tin về"]:
            product_name = product_name.replace(term, "")
        product_name = product_name.strip()
        
        search_result = product_search_chain.invoke({"question": product_name}, search_kwargs={"k": 5})
        
        # If no relevant results found in vector database, crawl from Tiki
        if "tôi sẽ tìm kiếm" in search_result.lower():
            logger.info(f"Search result: {search_result}")
            tiki_products = crawl_tiki_product(product_name)
            
            if tiki_products:                         
                # Start price comparison immediately with crawled data
                context_data = json.dumps(tiki_products, ensure_ascii=False)
                try:
                    comparison_result = price_comparison_chain({
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
                    for product in tiki_products:
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
                    products_vector_db.persist()
                    logger.info("Updated vector database with new products.")
                except Exception as e:
                    logger.error(f"Error updating vector database: {str(e)}")
                    logger.warning("Search data was processed but may not be stored.")

                return comparison_result
            else:
                return "Xin lỗi, tôi không tìm thấy thông tin về sản phẩm này trên Tiki. Vui lòng thử lại với từ khóa khác."
        
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