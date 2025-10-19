from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import users_api
import uvicorn

# Khởi tạo FastAPI app
app = FastAPI(
    title="RentAI API",
    description="API cho hệ thống quản lý bất động sản",
    version="1.0.0"
)

# Cấu hình CORS (nếu cần)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định cụ thể domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router từ users_api
app.include_router(users_api.router, prefix="/api", tags=["Users"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RentAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload khi code thay đổi (chỉ dùng trong dev)
    )
