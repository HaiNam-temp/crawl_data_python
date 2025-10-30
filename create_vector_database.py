import json
import dotenv
from datetime import datetime
from typing import List, Dict
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from logger_config import get_logger

logger = get_logger(__name__)

PRODUCTS_JSON_PATH = "C:/Users/ADMIN/Desktop/Le_Dinh_Dat/LSD/data/tiki_products_user_keywords.json"
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
                "title": product.get("title", ""),
                "image": product.get("image", ""),
                "price": product.get("price", ""),
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

def add_documents_to_vector_db(documents_data: List[Dict]):
    """
    Add new documents to existing vector database
    
    Args:
        documents_data: List of dicts with 'content' and 'metadata' keys
    """
    try:
        logger.info(f"Adding {len(documents_data)} documents to vector database")
        
        # Convert to Document objects
        documents = []
        for doc_data in documents_data:
            doc = Document(
                page_content=doc_data['content'],
                metadata=doc_data.get('metadata', {})
            )
            documents.append(doc)
        
        # Load existing vector store or create new one
        try:
            vector_store = Chroma(
                persist_directory=PRODUCTS_CHROMA_PATH,
                embedding_function=OpenAIEmbeddings()
            )
            # Add documents to existing store
            vector_store.add_documents(documents)
        except Exception:
            # If store doesn't exist, create new one
            vector_store = Chroma.from_documents(
                documents,
                OpenAIEmbeddings(),
                persist_directory=PRODUCTS_CHROMA_PATH
            )
        
        logger.info(f"Successfully added {len(documents)} documents to vector database")
        
    except Exception as e:
        logger.error(f"Error adding documents to vector database: {e}")


if __name__ == "__main__":
    initialize_vector_store()
