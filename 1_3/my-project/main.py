"""my-project — FastAPI 应用入口。

启动方式:
    python main.py                  # 直接运行
    uvicorn main:app --reload       # 开发模式（热重载）
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # 从 .env 加载环境变量（可选）

app = FastAPI(title=os.getenv("APP_NAME", "my-project"), version="0.1.0")


@app.get("/")
def read_root() -> dict:
    """根路由。"""
    return {"message": "Welcome to my-project!", "status": "ok"}


@app.get("/health")
def health_check() -> dict:
    """健康检查。"""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
