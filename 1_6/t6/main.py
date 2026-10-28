from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import agents_router
from collections import deque
from datetime import datetime
from pathlib import Path
import json
import os
import time

app = FastAPI(
    title="AI Agent 管理 API（t6：持久化 + 搜索 + 限流 + 审计）",
    description="在 1.6.7 CRUD 基础上：JSON 持久化、模糊搜索、IP 限流、操作审计",
    version="0.2.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 开发环境：允许所有来源
    allow_methods=["*"],
    allow_headers=["*"],
)

# 审计日志文件固定在 t6/ 下，与启动时的工作目录无关
AUDIT_LOG = Path(__file__).resolve().parent / "audit.log"

# 频率限制参数：默认满足题目要求（同一 IP 每 10 秒最多 5 次），
# 可用环境变量覆盖，方便压测时放开（如 RATE_LIMIT_MAX=1000）
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "5"))
RATE_LIMIT_WINDOW = float(os.environ.get("RATE_LIMIT_WINDOW", "10"))

# 每 IP 的请求时间戳（滑动窗口）。单进程单事件循环，无需加锁
_request_times: dict[str, deque[float]] = {}


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    print(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.3f}s)")
    return response


# 审计日志中间件：记录创建/更新操作的操作人、操作类型、时间
@app.middleware("http")
async def audit_write_ops(request: Request, call_next):
    response = await call_next(request)
    action = {"POST": "create", "PATCH": "update"}.get(request.method)
    # 只审计创建和更新，且只记录成功写入的（2xx）
    if action and request.url.path.startswith("/agents") and 200 <= response.status_code < 300:
        entry = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "user": request.headers.get("x-user", "anonymous"),
            "action": action,
            "path": request.url.path,
            "status": response.status_code,
        }
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[审计] {entry['user']} {entry['action']} {entry['path']}")
    return response


# 频率限制中间件：同一 IP 在滑动窗口内最多 RATE_LIMIT_MAX 次，超出返回 429
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    times = _request_times.setdefault(client_ip, deque())
    # 先淘汰窗口外的旧时间戳
    while times and now - times[0] > RATE_LIMIT_WINDOW:
        times.popleft()
    if len(times) >= RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429,
            content={"detail": f"请求过于频繁，同一 IP 每 {RATE_LIMIT_WINDOW:g} 秒最多 {RATE_LIMIT_MAX} 次，请稍后再试"},
        )
    times.append(now)
    return await call_next(request)


# 挂载路由
app.include_router(agents_router)


@app.get("/health")
async def health():
    """健康检查接口（部署时用于检测服务是否存活）"""
    return {"status": "healthy"}
