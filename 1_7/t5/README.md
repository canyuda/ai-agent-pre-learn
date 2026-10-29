# t5 — 完整工程初始化练习

从零搭一个带测试与 git 分支工作流的最小 FastAPI 服务：`/health` 健康检查端点。

## 目录结构

```text
t5/
├── app/
│   ├── __init__.py
│   ├── config.py       # pydantic-settings 配置（环境变量 / .env）
│   └── main.py         # FastAPI 应用与 /health 端点
├── tests/
│   └── test_health.py  # 验证 /health 返回 200
├── conftest.py         # 让 pytest 能导入 app 包
├── requirements.txt    # 4 个运行时直接依赖
├── requirements-dev.txt# pytest / httpx2 / ruff
└── .gitignore
```

## 环境搭建

```bash
python -m venv .venv
source .venv/Scripts/activate        # Git Bash；PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt  # 含运行时依赖 + 开发工具
```

## 运行

```bash
python -m uvicorn app.main:app --port 8500
curl http://127.0.0.1:8500/health
```

## 测试与 lint

```bash
pytest
ruff check .
```

## Git 工作流

main 首次提交工程骨架 → `feature/health-endpoint` 分支添加 /health 端点与测试 → `--no-ff` 合并回 main：

```bash
git log --oneline --graph --all
```
