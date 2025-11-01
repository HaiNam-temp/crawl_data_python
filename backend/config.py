"""Configuration - giữ nguyên từ main.py"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database path. Can be overridden with the environment variable DB_PATH.
# Default kept for local development to preserve existing behavior.
DB_PATH = os.getenv("DB_PATH", "chatbot_database.db")

# Token storage (in-memory)
active_tokens = {}
