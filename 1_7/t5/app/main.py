from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
)


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查，供存活探针使用。"""
    return {"status": "ok", "app": settings.app_name, "version": settings.version}
