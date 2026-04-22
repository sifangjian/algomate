from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.algomate.api.routes import router

app = FastAPI(title="算法学习助手 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "算法学习助手 API 服务已启动"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
