"""t6：完整 AI Agent API 数据模型（题面）

用 Pydantic 设计一整套 AI Agent 服务的 API 数据模型，至少包含：

请求端：
├── CreateAgentRequest     — 创建 Agent（名称、模型、系统提示、温度等）
├── ChatRequest            — 发送对话消息
├── ToolExecuteRequest     — 手动触发工具执行

响应端：
├── AgentResponse          — Agent 详情
├── ChatResponse           — 对话响应（含工具调用列表）
├── ToolExecuteResponse    — 工具执行结果
├── AgentListResponse      — Agent 列表（分页）
├── ErrorResponse          — 统一错误响应

枚举：
├── AgentStatus            — idle / running / waiting / completed / failed
├── MessageRole            — system / user / assistant / tool

要求：
- 所有请求模型用 extra="forbid"
- 敏感的 token 字段用 exclude=True 避免序列化泄露
- 至少一个 @field_validator 和一个 @model_validator
- 给关键字段都加上 description
- 三个以上嵌套模型
- 写一个测试脚本：构造一份完整请求 JSON → model_validate_json() → 序列化回 JSON → 对比字段

文件划分：enums.py / models.py（共享嵌套模型）/ request_models.py /
response_models.py / test_models.py
"""

from pydantic import BaseModel, Field, model_validator

from enums import MessageRole


class ToolDefinition(BaseModel):
    """注册给 Agent 的工具定义。"""

    name: str = Field(
        min_length=1,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="工具名（snake_case，模型按此名发起调用）",
    )
    description: str = Field(min_length=1, description="给模型阅读的用途说明")
    parameters: dict = Field(
        min_length=1, description="JSON Schema 格式的参数定义，不能为空字典"
    )


class Message(BaseModel):
    """一条对话消息。"""

    role: MessageRole = Field(description="消息角色：system / user / assistant / tool")
    content: str = Field(default="", description="消息正文")
    tool_call_id: str | None = Field(
        default=None, description="role 为 tool 时对应的调用 ID"
    )


class ToolCall(BaseModel):
    """模型发起的一次工具调用。"""

    call_id: str = Field(
        pattern=r"^call_[0-9a-f]{8}$", description="调用 ID，格式 call_ + 8 位十六进制"
    )
    name: str = Field(min_length=1, description="被调用的工具名")
    arguments: dict = Field(default_factory=dict, description="调用参数")


class ToolOutcome(BaseModel):
    """工具执行结果的公共部分。"""

    output: str = Field(default="", description="工具输出（成功时）")
    error: str | None = Field(default=None, description="失败原因（失败时）")
    duration_ms: float = Field(ge=0, description="执行耗时（毫秒）")

    @model_validator(mode="after")
    def _need_output_or_error(self) -> "ToolOutcome":
        if not self.output and not self.error:
            raise ValueError("output 和 error 至少要有一个非空")
        return self


class ToolCallResult(ToolCall, ToolOutcome):
    """对话中一次工具调用及其结果。"""


class Usage(BaseModel):
    """token 用量统计。"""

    prompt_tokens: int = Field(ge=0, description="提示词消耗的 token 数")
    completion_tokens: int = Field(ge=0, description="补全消耗的 token 数")
    total_tokens: int = Field(ge=0, description="总 token 数")

    @model_validator(mode="after")
    def _total_matches(self) -> "Usage":
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("total_tokens 必须等于 prompt_tokens + completion_tokens")
        return self
