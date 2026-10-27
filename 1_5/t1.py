"""t1：使用 Pydantic，定义一个 Book 模型：

- title：必填，至少 1 个字符
- author：必填，至少 1 个字符
- pages：可选，正整数
- genre：可选，默认 "unknown"

创建两个 Book 实例，一个完整、一个只填必填字段，分别调用 model_dump_json() 对比输出。
"""
from pydantic import BaseModel, Field


class Book(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    pages: int | None = Field(default=None, gt=0)
    genre: str = "unknown"


full = Book(title="三体", author="刘慈欣", pages=302, genre="科幻")
minimal = Book(title="活着", author="余华")

print("完整字段：", full.model_dump_json(indent=2))
print("仅必填字段：", minimal.model_dump_json(indent=2))
