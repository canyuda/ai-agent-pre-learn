# 1. 用类型注解定义参数 —— 自动校验 + 自动生成文档
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class HelloRequest(BaseModel):
    name: str
    times: int = 1

@app.post("/hello")
async def hello(req: HelloRequest):       # ← 你定义了类型，FastAPI 自动做校验
    return {"message": f"Hello {req.name}! " * req.times}
