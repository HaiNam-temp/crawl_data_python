"""Pydantic Models - giữ nguyên từ main.py"""
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_admin: bool = False
    created_at: str

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class Conversation(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str

class MessageCreate(BaseModel):
    content: str

class Message(BaseModel):
    id: str
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str

class PlatformCreate(BaseModel):
    name: str
    url: str
    status: str = "active"

class Platform(BaseModel):
    id: str
    name: str
    url: str
    status: str
    created_at: str


class ProductCreate(BaseModel):
    name: str
    price: Optional[float] = None
    url: str
    image: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    metadata: Optional[dict] = None


class Product(BaseModel):
    id: str
    name: str
    price: Optional[float] = None
    url: str
    image: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    metadata: Optional[dict] = None
    created_at: str
