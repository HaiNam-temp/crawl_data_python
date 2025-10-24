from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from operator import itemgetter
from typing import Any
import os
from logger_config import get_logger

logger = get_logger(__name__)

# Initialize ChatOpenAI (kept local to this module to avoid circular imports)
chat_model = ChatOpenAI(
    model="gpt-5",
    temperature=0
)

# Minimal vector DB setup for products retriever inside this module
PRODUCTS_CHROMA_PATH = "chroma_data/"
embedding_function = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-ada-002"
)
products_vector_db = Chroma(
    persist_directory=PRODUCTS_CHROMA_PATH,
    embedding_function=embedding_function
)
products_retriever = products_vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

def create_chain_with_template(system_template: str, human_template: str = "{question}"):
    """Helper function to create a chain with given templates"""
    logger.info("create_chain_with_template called (system_template len=%d, human_template len=%d)",
                len(system_template or ""), len(human_template or ""))
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
        logger.info("create_chain_with_template: returning retriever-based chain")
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
            logger.info("process_chain called with keys=%s", list((inputs or {}).keys()))
            logger.info("process_chain inputs: %s", str(inputs))
            try:
                result = chain.invoke(inputs)
                out = result["text"] if isinstance(result, dict) else str(result)
                logger.info("process_chain completed; output_len=%d", len(out) if out else 0)
                return out
            except Exception as e:
                logger.error("process_chain error: %s", str(e))
                raise ValueError(f"Error processing chain: {str(e)}")
        
        return process_chain
