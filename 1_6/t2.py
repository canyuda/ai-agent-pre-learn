"""练习 2：查询参数实战

在练习 1 基础上新增 GET /agents?page=1&size=10&model=gpt-4o
用 Query() 校验 page >= 1、size 在 1~100 之间，返回所有参数 + 模拟分页结果。
启动：cd 1_6 && ../.venv/bin/python -m uvicorn t2:app --port 8300
"""
from datetime import datetime

from fastapi import FastAPI, Query

app = FastAPI(title="练习2 · 查询参数实战")


@app.get("/")
async def root():
    return {"message": "Hello"}


@app.get("/time")
async def server_time():
    return {"server_time": datetime.now().isoformat(timespec="seconds")}


@app.get("/echo/{text}")
async def echo(text: str):
    return {"echo": text}


# 模拟数据源：当作数据库里的 Agent 表（50 条，model 交替两种值方便筛选）
FAKE_AGENTS = [
    {
        "id": i,
        "name": f"agent-{i}",
        "model": "gpt-4o" if i % 2 == 0 else "deepseek-chat",
    }
    for i in range(1, 51)
]


@app.get("/agents")
async def list_agents(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    size: int = Query(default=10, ge=1, le=100, description="每页数量，1-100"),
    model: str | None = Query(default=None, description="按模型筛选"),
):
    """分页查询 Agent 列表；参数不合法时 FastAPI 自动返回 422"""
    agents = FAKE_AGENTS
    if model:
        agents = [a for a in agents if a["model"] == model]

    total = len(agents)
    start = (page - 1) * size
    items = agents[start:start + size]

    return {
        "page": page,
        "size": size,
        "model": model,
        "total": total,
        "items": items,
    }
