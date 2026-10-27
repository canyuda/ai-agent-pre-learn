"""t6：AI Agent API 枚举定义。"""

from enum import Enum


class AgentStatus(str, Enum):
    """Agent 的生命周期状态。"""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """对话消息的角色。"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
