# my-project

FastAPI 项目骨架（由 scaffold.sh 生成）。

## 快速开始

    python -m venv .venv
    source .venv/Scripts/activate    # Windows (Git Bash)
    # source .venv/bin/activate      # Linux / macOS
    pip install -r requirements.txt
    python main.py

- 接口文档: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/health

## 目录结构

| 目录 | 用途 |
| ---- | ---- |
| src/my_project/ | 核心源码（api / core / services 分层） |
| tests/ | pytest 测试 |
| docs/ | 项目文档 |
| scripts/ | 运维 / 辅助脚本 |
| data/ | 本地数据（不入库） |
| config/ | 配置文件 |
| .github/workflows/ | CI 流水线 |

## 运行测试

    pytest -v
