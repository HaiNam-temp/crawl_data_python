"""
Sophie Chatbot API - Main Entry Point
File main.py đã được tách nhỏ thành các module trong thư mục backend/
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

try:
    from logger_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Import từ backend modules
from backend.database import init_database
from backend.routes import auth_routes, conversation_routes, admin_routes
# Initialize FastAPI app
app = FastAPI(
    title="Sophie Chatbot API",
    description="API for Sophie - AI Shopping Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("FastAPI application started")

# Register routers
app.include_router(auth_routes.router, tags=["Authentication"])
app.include_router(conversation_routes.router, tags=["Conversations"])
app.include_router(admin_routes.router, tags=["Admin"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sophie Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)
