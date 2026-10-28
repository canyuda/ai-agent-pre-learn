"""练习 3：请求体验证（Pydantic 模型）

POST /tasks：title 必填 1-200 字符；priority 可选 low/medium/high 默认 medium；
assignee 可选字符串。返回带模拟 ID 和时间戳的任务。
启动：cd 1_6 && ../.venv/bin/python -m uvicorn t3:app --port 8300
"""
import time
import uuid
from typing import Literal

from fastapi import FastAPI, status
from pydantic import BaseModel, Field

app = FastAPI(title="练习3 · 请求体验证")


class CreateTaskRequest(BaseModel):
    """请求体：校验失败时 FastAPI 自动返回 422 + 具体哪个字段错了"""

    title: str = Field(min_length=1, max_length=200, description="任务标题，1-200 字符")
    priority: Literal["low", "medium", "high"] = Field(
        default="medium", description="优先级，只能是三个枚举值之一"
    )
    assignee: str | None = Field(default=None, description="负责人，可选")


class TaskResponse(BaseModel):
    """响应体：服务端补充 ID 和时间戳"""

    id: str
    title: str
    priority: str
    assignee: str | None
    created_at: float


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: CreateTaskRequest):
    """创建任务：Pydantic 校验通过后才会进入函数体"""
    return TaskResponse(
        id=uuid.uuid4().hex[:8],
        title=request.title,
        priority=request.priority,
        assignee=request.assignee,
        created_at=time.time(),
    )
