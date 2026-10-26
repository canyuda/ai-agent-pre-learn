#!/usr/bin/env bash
# ============================================================================
# scaffold.sh — Python FastAPI 项目脚手架生成器
#
# 用法:
#   ./scaffold.sh <project-name>
#
# 功能:
#   1. 校验项目名称（必填，非法字符直接拒绝）
#   2. 创建标准 Python 项目骨架（src 分层 / tests / docs / scripts / data / config / CI）
#   3. 生成 main.py（FastAPI 最小示例）、requirements.txt、.gitignore、.env.example
#   4. 彩色日志: INFO=蓝色  OK=绿色  ERROR=红色
#   5. 完成后打印项目树状结构
# ============================================================================

set -euo pipefail

# ----------------------------------------------------------------------------
# 颜色与日志（非终端输出时自动禁用颜色，避免转义码污染重定向的日志）
# ----------------------------------------------------------------------------
if [[ -t 1 ]]; then
    readonly C_INFO=$'\033[1;34m'   # 蓝色
    readonly C_OK=$'\033[1;32m'     # 绿色
    readonly C_ERR=$'\033[1;31m'    # 红色
    readonly C_RESET=$'\033[0m'
else
    readonly C_INFO='' C_OK='' C_ERR='' C_RESET=''
fi

info()  { printf '%s[INFO]%s  %s\n'  "$C_INFO" "$C_RESET" "$*"; }
ok()    { printf '%s[ OK ]%s  %s\n'  "$C_OK"   "$C_RESET" "$*"; }
error() { printf '%s[ERROR]%s  %s\n' "$C_ERR"  "$C_RESET" "$*" >&2; }

# ----------------------------------------------------------------------------
# 帮助信息
# ----------------------------------------------------------------------------
usage() {
    cat <<USAGE
用法:
    $(basename "$0") <project-name>

描述:
    创建一个标准 Python FastAPI 项目骨架（src 分层 / tests / docs / CI）。

参数:
    project-name    项目名称（必填）。仅允许字母、数字、下划线、连字符，
                    且以字母或下划线开头；连字符会自动转换为包名下划线。

选项:
    -h, --help      显示本帮助信息并退出

示例:
    ./scaffold.sh my-project
    bash scaffold.sh demo_api
USAGE
}

# ----------------------------------------------------------------------------
# 参数解析
# ----------------------------------------------------------------------------
parse_args() {
    if [[ $# -eq 0 ]]; then
        error "缺少参数：必须提供项目名称"
        usage >&2
        exit 1
    fi

    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            error "未知选项: $1"
            usage >&2
            exit 1
            ;;
    esac

    if [[ $# -gt 1 ]]; then
        error "参数过多：仅需一个项目名称（收到 $# 个）"
        usage >&2
        exit 1
    fi

    PROJECT_NAME=$1
}

# ----------------------------------------------------------------------------
# 名称校验与包名换算
# ----------------------------------------------------------------------------
validate_name() {
    if [[ ! "$PROJECT_NAME" =~ ^[a-zA-Z_][a-zA-Z0-9_-]*$ ]]; then
        error "非法项目名称: '$PROJECT_NAME'"
        error "仅允许字母、数字、下划线和连字符，且以字母或下划线开头"
        exit 1
    fi
    # 连字符转下划线作为 Python 包名: my-project -> my_project
    PACKAGE_NAME="${PROJECT_NAME//-/_}"
}

ensure_target_available() {
    if [[ -e "$PROJECT_NAME" ]]; then
        error "目标已存在，拒绝覆盖: $PROJECT_NAME"
        exit 1
    fi
}

# ----------------------------------------------------------------------------
# 目录与文件生成
# ----------------------------------------------------------------------------
create_dirs() {
    local -a dirs=(
        "src/${PACKAGE_NAME}/api"
        "src/${PACKAGE_NAME}/core"
        "src/${PACKAGE_NAME}/services"
        "tests"
        "docs"
        "scripts"
        "data"
        "config"
        ".github/workflows"
    )
    local d
    for d in "${dirs[@]}"; do
        mkdir -p "$PROJECT_NAME/$d"
        info "创建目录: $PROJECT_NAME/$d"
    done
}

# 用法: write_file <相对路径>，文件内容从 heredoc (stdin) 读取
write_file() {
    local path="$PROJECT_NAME/$1"
    cat > "$path"
    ok "生成文件: $path"
}

touch_empty() {
    local path="$PROJECT_NAME/$1"
    : > "$path"
    ok "生成文件: $path"
}

generate_files() {
    # ---------- main.py：FastAPI 最小示例 ----------
    write_file "main.py" <<EOF
"""$PROJECT_NAME — FastAPI 应用入口。

启动方式:
    python main.py                  # 直接运行
    uvicorn main:app --reload       # 开发模式（热重载）
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # 从 .env 加载环境变量（可选）

app = FastAPI(title=os.getenv("APP_NAME", "$PROJECT_NAME"), version="0.1.0")


@app.get("/")
def read_root() -> dict:
    """根路由。"""
    return {"message": "Welcome to $PROJECT_NAME!", "status": "ok"}


@app.get("/health")
def health_check() -> dict:
    """健康检查。"""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
EOF

    # ---------- requirements.txt ----------
    write_file "requirements.txt" <<'EOF'
# ---- 运行时依赖 ----
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-dotenv>=1.0.1

# ---- 开发 / 测试依赖 ----
pytest>=8.3.0
httpx>=0.27.0
EOF

    # ---------- .gitignore ----------
    write_file ".gitignore" <<'EOF'
# ---- Python ----
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# ---- 虚拟环境 ----
.venv/
venv/

# ---- 环境变量（保留模板） ----
.env
.env.*
!.env.example

# ---- 测试 / 覆盖率 ----
.pytest_cache/
.coverage
htmlcov/

# ---- IDE / 编辑器 ----
.idea/
.vscode/

# ---- 日志 ----
*.log

# ---- 数据目录（保留占位文件） ----
data/*
!data/.gitkeep

# ---- 操作系统 ----
.DS_Store
Thumbs.db
EOF

    # ---------- .env.example ----------
    write_file ".env.example" <<EOF
# 复制为 .env 并按需修改: cp .env.example .env

# ---- 应用 ----
APP_NAME=$PROJECT_NAME
APP_ENV=development

# ---- 服务 ----
HOST=0.0.0.0
PORT=8000

# ---- 日志: DEBUG / INFO / WARNING / ERROR ----
LOG_LEVEL=INFO
EOF

    # ---------- pyproject.toml ----------
    write_file "pyproject.toml" <<EOF
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "$PACKAGE_NAME"
version = "0.1.0"
description = "$PROJECT_NAME — FastAPI service"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF

    # ---------- README.md ----------
    write_file "README.md" <<EOF
# $PROJECT_NAME

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
| src/$PACKAGE_NAME/ | 核心源码（api / core / services 分层） |
| tests/ | pytest 测试 |
| docs/ | 项目文档 |
| scripts/ | 运维 / 辅助脚本 |
| data/ | 本地数据（不入库） |
| config/ | 配置文件 |
| .github/workflows/ | CI 流水线 |

## 运行测试

    pytest -v
EOF

    # ---------- src 包 ----------
    write_file "src/${PACKAGE_NAME}/__init__.py" <<EOF
"""$PROJECT_NAME 核心包。"""

__version__ = "0.1.0"
EOF

    touch_empty "src/${PACKAGE_NAME}/api/__init__.py"
    touch_empty "src/${PACKAGE_NAME}/core/__init__.py"
    touch_empty "src/${PACKAGE_NAME}/services/__init__.py"

    write_file "src/${PACKAGE_NAME}/api/routes.py" <<'EOF'
"""业务路由示例：在 main.py 中通过 include_router 挂载。"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/ping")
def ping() -> dict:
    """示例接口。"""
    return {"pong": True}
EOF

    write_file "src/${PACKAGE_NAME}/core/config.py" <<EOF
"""集中管理应用配置（后续可升级为 pydantic-settings）。"""

import os

APP_NAME = os.getenv("APP_NAME", "$PROJECT_NAME")
DEBUG = os.getenv("APP_ENV", "development") == "development"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
EOF

    # ---------- tests ----------
    touch_empty "tests/__init__.py"

    write_file "tests/test_main.py" <<'EOF'
"""main.py 接口冒烟测试。"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_check() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
EOF

    # ---------- 其他资源 ----------
    write_file "docs/index.md" <<EOF
# $PROJECT_NAME 文档

- 项目简介: TODO
- 架构设计: TODO
EOF

    write_file ".github/workflows/ci.yml" <<'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: 安装依赖
        run: pip install -r requirements.txt
      - name: 运行测试
        run: pytest -v
EOF

    touch_empty "scripts/.gitkeep"
    touch_empty "data/.gitkeep"
    touch_empty "config/.gitkeep"
}

# ----------------------------------------------------------------------------
# 树状结构打印（Git Bash 无 tree 命令，纯 Bash 递归实现）
# ----------------------------------------------------------------------------
print_tree() {
    local base=$1 prefix=$2
    local -a entries=()
    local item connector new_prefix i total

    # 列出当前层条目（含隐藏文件），排除 .git，按名称排序
    # find 输出的是完整路径，用 ${item##*/} 剥离目录前缀，只保留条目名
    while IFS= read -r -d '' item; do
        entries+=("${item##*/}")
    done < <(find "$base" -mindepth 1 -maxdepth 1 -name '.git' -prune -o -print0 | LC_ALL=C sort -z)

    total=${#entries[@]}
    for ((i = 0; i < total; i++)); do
        item="${entries[$i]}"
        if ((i == total - 1)); then
            connector='└── '
            new_prefix="${prefix}    "
        else
            connector='├── '
            new_prefix="${prefix}│   "
        fi
        printf '%s%s%s\n' "$prefix" "$connector" "$item"
        if [[ -d "$base/$item" ]]; then
            print_tree "$base/$item" "$new_prefix"
        fi
    done
}

print_project_tree() {
    info "项目结构:"
    printf '%s/\n' "$PROJECT_NAME"
    print_tree "$PROJECT_NAME" ""
}

print_next_steps() {
    printf '\n'
    ok "项目 '$PROJECT_NAME' 创建完成！"
    printf '\n'
    info "后续步骤:"
    cat <<STEPS
  1. cd $PROJECT_NAME
  2. python -m venv .venv && source .venv/Scripts/activate    # Windows (Git Bash)
  3. pip install -r requirements.txt
  4. python main.py    ->    http://127.0.0.1:8000/docs
STEPS
}

# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
main() {
    parse_args "$@"
    validate_name
    ensure_target_available

    info "开始创建项目: $PROJECT_NAME（Python 包名: $PACKAGE_NAME）"
    create_dirs
    generate_files
    print_project_tree
    print_next_steps
}

main "$@"
