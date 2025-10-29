"""Configuration - giữ nguyên từ main.py"""
from dotenv import load_dotenv

load_dotenv()

# Database
DB_PATH = "chatbot_database.db"

# Token storage
active_tokens = {}
