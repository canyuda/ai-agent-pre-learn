"""t2：改进上一题的 Book 模型：

- pages 必须在 1~10000 之间
- 添加 isbn 字段，用正则校验格式（978- 开头，格式 978-X-XXXX-XXXX-X）
- 加 @field_validator：title 自动去首尾空格
- 测试传错误参数时 Pydantic 报的错
"""
from pydantic import BaseModel, Field, ValidationError, field_validator


class Book(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    pages: int | None = Field(default=None, ge=1, le=10000)
    genre: str = "unknown"
    isbn: str = Field(pattern=r"^978-\d-\d{4}-\d{4}-\d$")

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()


print(Book(title="  三体  ", author="刘慈欣", pages=302, genre="科幻",
           isbn="978-7-5366-9293-0").model_dump_json(indent=2))

for bad in [
    dict(title="三体", author="刘慈欣", isbn="978-7-5366-9293-0", pages=0),
    dict(title="三体", author="刘慈欣", isbn="978-7-5366-9293-0", pages=10001),
    dict(title="  ", author="刘慈欣", isbn="978-7-5366-9293-0"),
    dict(title="三体", author="刘慈欣", isbn="123-4-5678-9012-3"),
]:
    try:
        Book(**bad)
    except ValidationError as e:
        print(f"\n输入 {bad}\n{e}")
