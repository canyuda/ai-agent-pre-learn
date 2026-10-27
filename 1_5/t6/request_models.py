"""t6：请求端模型。所有请求模型 extra="forbid"，拒绝未知字段。"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from enums import MessageRole
from models import Message, ToolDefinition


class StrictRequest(BaseModel):
    """请求模型基类：多余字段直接报错，防止拼写错误被静默忽略。"""

    model_config = ConfigDict(extra="forbid")


class CreateAgentRequest(StrictRequest):
    """创建 Agent。"""

    name: str = Field(
        min_length=1, max_length=64, description="Agent 名称，自动去除首尾空格"
    )
    model: str = Field(
        min_length=1,
        pattern=r"^[A-Za-z0-9._:-]+$",
        description="模型 ID，如 claude-sonnet-5",
    )
    system_prompt: str = Field(default="", description="系统提示词")
    temperature: float = Field(default=0.7, ge=0, le=2, description="采样温度 0~2")
    max_tokens: int = Field(
        default=2048, ge=1, le=128_000, description="单次回复最大 token 数"
    )
    tools: list[ToolDefinition] = Field(
        default_factory=list, description="注册给该 Agent 的工具列表"
    )
    api_token: str | None = Field(
        default=None,
        exclude=True,
        repr=False,
        description="调用方凭证；exclude=True 使其不参与序列化，避免泄露",
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class ChatRequest(StrictRequest):
    """发送对话消息。"""

    agent_id: str = Field(
        pattern=r"^agt_[0-9a-f]{8}$", description="目标 Agent ID"
    )
    messages: list[Message] = Field(min_length=1, description="完整对话历史")
    stream: bool = Field(default=False, description="是否流式返回")
    api_token: str | None = Field(
        default=None, exclude=True, repr=False, description="调用方凭证，不序列化"
    )

    @model_validator(mode="after")
    def _check_messages(self) -> "ChatRequest":
        if self.messages[-1].role is not MessageRole.USER:
            raise ValueError("对话请求的最后一条消息必须是 user")
        for m in self.messages:
            if m.role is MessageRole.TOOL and not m.tool_call_id:
                raise ValueError("role=tool 的消息必须带 tool_call_id")
        return self


class ToolExecuteRequest(StrictRequest):
    """手动触发一次工具执行（调试 / 回放用）。"""

    agent_id: str = Field(pattern=r"^agt_[0-9a-f]{8}$", description="目标 Agent ID")
    tool_name: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$", description="要执行的工具名"
    )
    arguments: dict = Field(default_factory=dict, description="传给工具的参数")
    timeout_ms: int = Field(
        default=30_000, ge=100, le=600_000, description="执行超时（毫秒）"
    )
    api_token: str | None = Field(
        default=None, exclude=True, repr=False, description="调用方凭证，不序列化"
    )
