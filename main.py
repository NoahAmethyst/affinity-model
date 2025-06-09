from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
from dotenv import load_dotenv

from api.affinity import affinity_model

# 初始化 FastAPI 应用
app = FastAPI(
    title="示例API服务",
    description="这是一个使用FastAPI构建的示例HTTP服务",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # Load .env file
    load_dotenv()
    app.include_router(affinity_model)
    uvicorn.run(app, host="0.0.0.0", port=9554)