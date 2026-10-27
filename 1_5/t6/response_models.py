"""t6：响应端模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from enums import AgentStatus
from models import Message, ToolCallResult, ToolOutcome, Usage


class AgentResponse(BaseModel):
    """Agent 详情。"""

    id: str = Field(pattern=r"^agt_[0-9a-f]{8}$", description="Agent ID")
    name: str = Field(description="Agent 名称")
    model: str = Field(description="使用的模型 ID")
    system_prompt: str = Field(default="", description="系统提示词")
    temperature: float = Field(description="采样温度")
    status: AgentStatus = Field(description="当前状态")
    created_at: datetime = Field(description="创建时间（ISO 8601）")
    updated_at: datetime | None = Field(default=None, description="最后更新时间")


class ChatResponse(BaseModel):
    """对话响应，含本轮的工具调用列表。"""

    id: str = Field(description="本轮对话 ID")
    agent_id: str = Field(description="Agent ID")
    message: Message = Field(description="模型回复的消息")
    tool_calls: list[ToolCallResult] = Field(
        default_factory=list, description="本轮发起的工具调用及执行结果"
    )
    usage: Usage = Field(description="token 用量")
    finish_reason: Literal["stop", "tool_calls", "length"] = Field(
        default="stop", description="结束原因"
    )


class ToolExecuteResponse(ToolOutcome):
    """手动工具执行的结果。"""

    call_id: str = Field(pattern=r"^call_[0-9a-f]{8}$", description="调用 ID")


class AgentListResponse(BaseModel):
    """Agent 分页列表。"""

    items: list[AgentResponse] = Field(description="当前页的 Agent")
    total: int = Field(ge=0, description="总数")
    page: int = Field(ge=1, description="当前页码，从 1 开始")
    page_size: int = Field(ge=1, le=100, description="每页数量")
    has_more: bool = Field(description="是否还有下一页")


class ErrorResponse(BaseModel):
    """统一错误响应。"""

    code: str = Field(description="机器可读错误码，如 validation_error")
    message: str = Field(description="人类可读错误信息")
    details: dict | None = Field(default=None, description="附加信息（如字段级错误）")
    request_id: str | None = Field(default=None, description="请求追踪 ID")
