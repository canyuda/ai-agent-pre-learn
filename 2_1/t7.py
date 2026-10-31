"""
JSON Schema 实战： 为"发邮件"这个工具写一个 JSON Schema。工具参数包括：
to：收件人邮箱（必填，字符串）
subject：邮件主题（必填，字符串）
body：邮件正文（必填，字符串）
cc：抄送（可选，字符串数组）
priority：优先级（可选，只能是 “low” / “normal” / “high” 之一，默认 “normal”）
分别用纯 JSON Schema 和 Pydantic 各写一版。
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class SendEmailRequest(BaseModel):
    """Arguments for the send_email tool."""

    to: EmailStr                                   # required + real email check
    subject: str = Field(min_length=1)             # required non-empty
    body: str
    cc: list[str] | None = None                    # optional, list of strings
    priority: Literal["low", "normal", "high"] = "normal"

    model_config = {"extra": "forbid"}             # reject unknown params