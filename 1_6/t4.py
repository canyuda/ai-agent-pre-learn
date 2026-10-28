"""练习 4：Depends 认证（API Key）

verify_admin 依赖函数校验请求头 X-Admin-Key；
GET /public 无需认证，GET /admin 必须携带正确的 Key，错误的 Key 返回 401。
启动：cd 1_6 && ../.venv/bin/python -m uvicorn t4:app --port 8300
"""
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI(title="练习4 · Depends 认证")

# 演示用的合法 Key（真实项目从环境变量/配置中心读取，绝不硬编码真密钥）
VALID_ADMIN_KEY = "admin-key-demo"


async def verify_admin(key: str = Header(alias="X-Admin-Key")):
    """依赖函数：Header(alias=...) 把下划线参数名映射到请求头 X-Admin-Key"""
    if key != VALID_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="无效的 Admin Key")
    return key


@app.get("/public")
async def public():
    """公开接口：不挂依赖，任何人可访问"""
    return {"message": "这是公开接口，任何人都能访问"}


@app.get("/admin", dependencies=[Depends(verify_admin)])
async def admin():
    """管理接口：dependencies=[...] 只做校验，不需要依赖函数的返回值"""
    return {"message": "欢迎回来，管理员", "data": "这是受保护的机密数据"}
