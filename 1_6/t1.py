"""练习 1：第一个 FastAPI 服务

三个端点：GET / 、GET /time 、GET /echo/{text}
启动：cd 1_6 && ../.venv/bin/python -m uvicorn t1:app --port 8300
"""
from datetime import datetime

from fastapi import FastAPI

app = FastAPI(title="练习1 · 第一个 FastAPI 服务")


@app.get("/")
async def root():
    """返回问候语"""
    return {"message": "Hello"}


@app.get("/time")
async def server_time():
    """返回当前服务器时间（ISO 8601 格式，精确到秒）"""
    return {"server_time": datetime.now().isoformat(timespec="seconds")}


@app.get("/echo/{text}")
async def echo(text: str):
    """路径参数：声明在 URL 里，函数参数同名自动绑定"""
    return {"echo": text}
