"""Conversation & Message routes - giữ nguyên từ main.py"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Import chatbot
try:
    from chatbot import process_user_query
    CHATBOT_AVAILABLE = True
except ImportError as e:
    CHATBOT_AVAILABLE = False
    print(f"Warning: Chatbot not available: {e}")
    def process_user_query(query: str) -> str:
        return "Chatbot is not configured. Please check dependencies."

from ..database import get_db
from ..auth import get_current_user
from ..models import ConversationCreate, Conversation, Message, ChatRequest, ChatResponse

router = APIRouter()

@router.post("/conversations/", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new conversation"""
    conn = get_db()
    cursor = conn.cursor()
    
    conversation_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO conversations (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (conversation_id, current_user["id"], conversation.title, created_at, created_at))
    
    conn.commit()
    conn.close()
    
    logger.info(f"New conversation created: {conversation_id} by user {current_user['username']}")
    
    return Conversation(
        id=conversation_id,
        user_id=current_user["id"],
        title=conversation.title,
        created_at=created_at,
        updated_at=created_at
    )

@router.get("/conversations/", response_model=List[Conversation])
async def get_conversations(current_user: Dict = Depends(get_current_user)):
    """Get all conversations for current user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM conversations 
        WHERE user_id = ? 
        ORDER BY updated_at DESC
    """, (current_user["id"],))
    conversations = cursor.fetchall()
    conn.close()
    
    return [
        Conversation(
            id=conv["id"],
            user_id=conv["user_id"],
            title=conv["title"],
            created_at=conv["created_at"],
            updated_at=conv["updated_at"]
        )
        for conv in conversations
    ]

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get a specific conversation"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM conversations 
        WHERE id = ? AND user_id = ?
    """, (conversation_id, current_user["id"]))
    conversation = cursor.fetchone()
    conn.close()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return Conversation(
        id=conversation["id"],
        user_id=conversation["user_id"],
        title=conversation["title"],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"]
    )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a conversation"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if conversation exists and belongs to user
    cursor.execute("""
        SELECT * FROM conversations 
        WHERE id = ? AND user_id = ?
    """, (conversation_id, current_user["id"]))
    conversation = cursor.fetchone()
    
    if not conversation:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Delete messages first
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    
    # Delete conversation
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Conversation deleted: {conversation_id}")
    return None

@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(
    conversation_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get all messages in a conversation"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify conversation belongs to user
    cursor.execute("""
        SELECT * FROM conversations 
        WHERE id = ? AND user_id = ?
    """, (conversation_id, current_user["id"]))
    conversation = cursor.fetchone()
    
    if not conversation:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    cursor.execute("""
        SELECT * FROM messages 
        WHERE conversation_id = ? 
        ORDER BY created_at ASC
    """, (conversation_id,))
    messages = cursor.fetchall()
    conn.close()
    
    return [
        Message(
            id=msg["id"],
            conversation_id=msg["conversation_id"],
            role=msg["role"],
            content=msg["content"],
            created_at=msg["created_at"]
        )
        for msg in messages
    ]

@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: str,
    chat_request: ChatRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Send a message and get AI response"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify conversation belongs to user
    cursor.execute("""
        SELECT * FROM conversations 
        WHERE id = ? AND user_id = ?
    """, (conversation_id, current_user["id"]))
    conversation = cursor.fetchone()
    
    if not conversation:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message
    user_message_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_message_id, conversation_id, "user", chat_request.message, created_at))
    
    # Get AI response using chatbot
    try:
        ai_response = process_user_query(chat_request.message)
    except Exception as e:
        # Log full exception with stack trace and context to help debugging
        try:
            logger.exception(
                "Error processing query for conversation %s user %s: %s | message: %s",
                conversation_id, current_user.get('username'), str(e), chat_request.message
            )
        except Exception:
            # Fallback in case logger.exception itself fails
            logger.error("Error processing query and failed to log exception details.", exc_info=True)
        ai_response = "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."
    
    # Save AI response
    assistant_message_id = str(uuid.uuid4())
    assistant_created_at = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (assistant_message_id, conversation_id, "assistant", ai_response, assistant_created_at))
    
    # Update conversation updated_at
    cursor.execute("""
        UPDATE conversations 
        SET updated_at = ? 
        WHERE id = ?
    """, (assistant_created_at, conversation_id))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Chat message processed in conversation {conversation_id}")
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        message_id=assistant_message_id
    )
