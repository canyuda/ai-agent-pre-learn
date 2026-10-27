"""t6：测试脚本 —— 请求 JSON → model_validate_json() → 序列化回 JSON → 对比字段。"""

import json

from pydantic import ValidationError

from enums import AgentStatus, MessageRole
from request_models import ChatRequest, CreateAgentRequest, ToolExecuteRequest
from response_models import (
    AgentListResponse,
    AgentResponse,
    ChatResponse,
    ErrorResponse,
    ToolExecuteResponse,
)

CREATE_JSON = """
{
  "name": "  天气助手  ",
  "model": "claude-sonnet-5",
  "system_prompt": "你是一个天气助手，回答前先调用 get_weather。",
  "temperature": 0.2,
  "max_tokens": 1024,
  "tools": [
    {
      "name": "get_weather",
      "description": "查询城市天气",
      "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
      }
    }
  ],
  "api_token": "sk-SECRET-should-not-leak"
}
"""

CHAT_JSON = """
{
  "agent_id": "agt_0a1b2c3d",
  "messages": [
    {"role": "system", "content": "你是天气助手"},
    {"role": "user", "content": "北京今天多少度？"}
  ],
  "stream": false,
  "api_token": "sk-SECRET-should-not-leak"
}
"""

TOOL_JSON = """
{
  "agent_id": "agt_0a1b2c3d",
  "tool_name": "get_weather",
  "arguments": {"city": "北京"},
  "timeout_ms": 5000,
  "api_token": "sk-SECRET-should-not-leak"
}
"""


def roundtrip(name: str, model_cls, raw: str) -> dict:
    """校验 JSON、序列化回来，打印差异并做断言。"""
    obj = model_cls.model_validate_json(raw)
    dumped = json.loads(obj.model_dump_json())

    print(f"\n=== {name} ===")
    print("解析结果:", obj)
    print("序列化后:", json.dumps(dumped, ensure_ascii=False))

    # token 不得出现在序列化输出中
    assert "api_token" not in dumped, f"{name}: api_token 泄露了！"
    assert "SECRET" not in json.dumps(dumped), f"{name}: token 值泄露了！"
    return dumped


def test_create_agent() -> None:
    dumped = roundtrip("CreateAgentRequest", CreateAgentRequest, CREATE_JSON)
    assert dumped["name"] == "天气助手", "name 应已去掉首尾空格"
    assert dumped["temperature"] == 0.2
    assert dumped["tools"][0]["name"] == "get_weather"
    assert dumped["max_tokens"] == 1024
    assert "system_prompt" in dumped


def test_chat_request() -> None:
    dumped = roundtrip("ChatRequest", ChatRequest, CHAT_JSON)
    assert dumped["agent_id"] == "agt_0a1b2c3d"
    assert [m["role"] for m in dumped["messages"]] == ["system", "user"]
    assert dumped["stream"] is False


def test_tool_execute() -> None:
    dumped = roundtrip("ToolExecuteRequest", ToolExecuteRequest, TOOL_JSON)
    assert dumped["arguments"] == {"city": "北京"}
    assert dumped["timeout_ms"] == 5000


def test_responses_roundtrip() -> None:
    agent = AgentResponse(
        id="agt_0a1b2c3d",
        name="天气助手",
        model="claude-sonnet-5",
        temperature=0.2,
        status=AgentStatus.IDLE,
        created_at="2026-10-27T10:00:00Z",
    )
    chat = ChatResponse(
        id="msg_1",
        agent_id="agt_0a1b2c3d",
        message={"role": MessageRole.ASSISTANT, "content": "北京 18 度"},
        usage={"prompt_tokens": 20, "completion_tokens": 8, "total_tokens": 28},
    )
    tool = ToolExecuteResponse(
        call_id="call_deadbeef", output='{"temp": 18}', duration_ms=12.5
    )
    listing = AgentListResponse(
        items=[agent], total=1, page=1, page_size=10, has_more=False
    )
    err = ErrorResponse(code="validation_error", message="参数错误")

    for obj in (agent, chat, tool, listing, err):
        back = type(obj).model_validate_json(obj.model_dump_json())
        print(f"{type(obj).__name__}: 往返一致 -> {back == obj}")
        assert back == obj, f"{type(obj).__name__} 序列化往返后不一致"


def test_rejections() -> None:
    """所有请求模型都应拒绝未知字段，并触发各自的校验器。"""
    bad_cases = [
        (
            "未知字段",
            CreateAgentRequest,
            CREATE_JSON.replace('"temperature": 0.2,', '"temperature": 0.2, "temp": 9,'),
        ),
        (
            "温度越界",
            CreateAgentRequest,
            CREATE_JSON.replace('"temperature": 0.2', '"temperature": 5'),
        ),
        (
            "最后一条不是 user",
            ChatRequest,
            CHAT_JSON.replace(
                '{"role": "user", "content": "北京今天多少度？"}',
                '{"role": "assistant", "content": "18 度"}',
            ),
        ),
        (
            "tool 消息缺 tool_call_id",
            ChatRequest,
            CHAT_JSON.replace(
                '{"role": "system", "content": "你是天气助手"}',
                '{"role": "tool", "content": "18"}',
            ),
        ),
        (
            "工具参数为空",
            CreateAgentRequest,
            json.dumps(
                {
                    "name": "x",
                    "model": "claude-sonnet-5",
                    "tools": [
                        {"name": "t", "description": "d", "parameters": {}}
                    ],
                }
            ),
        ),
    ]
    for label, cls, raw in bad_cases:
        try:
            cls.model_validate_json(raw)
        except ValidationError as e:
            print(f"\n[{label}] 已拒绝 -> {e.errors()[0]['type']}: {e.errors()[0]['msg']}")
        else:
            raise AssertionError(f"[{label}] 本应报错却通过了")


if __name__ == "__main__":
    test_create_agent()
    test_chat_request()
    test_tool_execute()
    test_responses_roundtrip()
    test_rejections()
    print("\n全部测试通过")
