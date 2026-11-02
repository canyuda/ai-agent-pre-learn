"""API Key 鉴权依赖（复制自 1_6/t5.py 练习 5，使 t2 目录独立可运行）

verify_admin 是 FastAPI 的依赖函数：Key 正确时原样返回，错误时抛业务异常。
"""
from fastapi import Header

# 演示用的合法 Key（真实项目从环境变量/配置中心读取，绝不硬编码真密钥）
VALID_ADMIN_KEY = "admin-key-demo"


class AdminAccessDenied(Exception):
    """管理员鉴权失败的业务异常（类比 Java 的自定义 Exception 子类）"""


async def verify_admin(key: str = Header(alias="X-Admin-Key")):
    """Header(alias=...) 把下划线参数名映射到请求头 X-Admin-Key"""
    if key != VALID_ADMIN_KEY:
        raise AdminAccessDenied("无效的 Admin Key")
    return key
