"""练习 5：异常处理 —— 在练习 4 基础上自定义异常 + 全局处理器

错误的 Key 访问 /admin 时，返回统一的 {"error": "ADMIN_ACCESS_DENIED", "detail": "..."}
而不是 FastAPI 默认的 {"detail": "..."} 格式。
启动：cd 1_6 && ../.venv/bin/python -m uvicorn t5:app --port 8300
"""
from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="练习5 · 自定义异常处理")

VALID_ADMIN_KEY = "admin-key-demo"


class AdminAccessDenied(Exception):
    """管理员鉴权失败的业务异常（类比 Java 的自定义 Exception 子类）"""


async def verify_admin(key: str = Header(alias="X-Admin-Key")):
    """不再抛 HTTPException，改抛业务异常，让响应格式与框架默认值解耦"""
    if key != VALID_ADMIN_KEY:
        raise AdminAccessDenied("无效的 Admin Key")
    return key


@app.exception_handler(AdminAccessDenied)
async def admin_access_denied_handler(request: Request, exc: AdminAccessDenied):
    """全局异常处理器：任何地方抛出 AdminAccessDenied 都会进入这里，统一转成固定 JSON"""
    return JSONResponse(
        status_code=401,
        content={"error": "ADMIN_ACCESS_DENIED", "detail": str(exc)},
    )


@app.get("/public")
async def public():
    return {"message": "这是公开接口，任何人都能访问"}


@app.get("/admin", dependencies=[Depends(verify_admin)])
async def admin():
    return {"message": "欢迎回来，管理员", "data": "这是受保护的机密数据"}
