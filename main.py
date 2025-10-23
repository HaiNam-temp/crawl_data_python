from fastapi import FastAPI
from app.apis.product_api import router as product_router

app = FastAPI(title="Crawl Data Service")
app.include_router(product_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
import sys