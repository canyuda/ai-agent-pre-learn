"""t4：工具参数模型 —— 设计一个 Agent 工具调用的数据模型：

- ToolDefinition（工具定义，注册时使用）：name / description / parameters（JSON Schema 格式的参数定义）
- ToolCall（工具调用，运行时使用）：id / name / arguments
- ToolResult（工具调用结果）：call_id / output / error / duration_ms

约束：
- ToolDefinition.parameters 不能为空字典
- ToolCall.id 用正则校验格式（call_ 前缀 + 8 位 hex）
- ToolResult 用 @model_validator(mode="after") 确保 error 和 output 至少有一个非空
"""
from typing import Optional

from pydantic import BaseModel, Field, ValidationError, model_validator


class ToolDefinition(BaseModel):
    """工具定义（注册时使用）"""
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict = Field(min_length=1)  # 空字典 {} 不合法


class ToolCall(BaseModel):
    """工具调用（运行时使用）"""
    id: str = Field(pattern=r"^call_[0-9a-f]{8}$")
    name: str = Field(min_length=1)
    arguments: dict = Field(default_factory=dict)


class ToolResult(BaseModel):
    """工具调用结果"""
    call_id: str = Field(min_length=1)
    output: str = ""
    error: Optional[str] = None
    duration_ms: float = Field(ge=0)

    @model_validator(mode="after")
    def check_payload(self) -> "ToolResult":
        if not self.output and not self.error:
            raise ValueError("output 和 error 至少要有一个非空")
        return self


if __name__ == "__main__":
    demo = ToolDefinition(
        name="get_weather",
        description="查询指定城市的天气",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}},
    )
    call = ToolCall(id="call_1a2b3c4d", name="get_weather", arguments={"city": "北京"})
    result = ToolResult(call_id=call.id, output='{"temp": 18}', duration_ms=120.5)
    print(demo.model_dump_json())
    print(call.model_dump_json())
    print(result.model_dump_json())

    for bad in [
        ("parameters 空", ToolDefinition, dict(name="x", description="y", parameters={})),
        ("id 格式错", ToolCall, dict(id="12345678", name="get_weather")),
        ("output/error 全空", ToolResult, dict(call_id="call_1a2b3c4d", output="", duration_ms=1.0)),
    ]:
        label, cls, kwargs = bad
        try:
            cls(**kwargs)
        except ValidationError as e:
            print(f"\n[{label}]\n{e}")
