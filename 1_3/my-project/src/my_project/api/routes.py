"""业务路由示例：在 main.py 中通过 include_router 挂载。"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/ping")
def ping() -> dict:
    """示例接口。"""
    return {"pong": True}
