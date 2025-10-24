import json
import dotenv
from datetime import datetime
from typing import List, Dict
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from logger_config import get_logger

logger = get_logger(__name__)

PRODUCTS_JSON_PATH = "data/tiki_products_user_keywords.json"
PRODUCTS_CHROMA_PATH = "chroma_data"

dotenv.load_dotenv()

def load_products_from_json() -> List[Dict]:
    """Load product data from JSON file"""
    with open(PRODUCTS_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_documents_from_products(products: List[Dict]) -> List[Document]:
    """Convert product data to Document objects for vector store"""
    documents = []
    for product in products:
        # Convert product dict to string for embedding
        product_text = json.dumps(product, ensure_ascii=False)
        doc = Document(
            page_content=product_text,
            metadata={
                "product_id": product.get("id", ""),
                "platform": product.get("platform", ""),
                "category": product.get("category", ""),
                "timestamp": datetime.now().isoformat()
            }
        )
        documents.append(doc)
    return documents

def initialize_vector_store():
    logger.info("initialize_vector_store called")
    try:
        # Load product data
        products = load_products_from_json()

        # Convert to documents
        documents = create_documents_from_products(products)

        # Create and persist vector store
        vector_store = Chroma.from_documents(
            documents,
            OpenAIEmbeddings(),
            persist_directory=PRODUCTS_CHROMA_PATH
        )

        logger.info("Successfully created vector store with %d products", len(documents))
        return vector_store

    except Exception as e:
        logger.error("Error creating vector store: %s", str(e))
        return None

if __name__ == "__main__":
    initialize_vector_store()
