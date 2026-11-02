"""t6 集成测试的公共 fixture。

- conftest.py 放在 t6/ 根目录：pytest 会把 conftest 所在目录加入 sys.path，
  tests/ 下的用例才能直接 `from main import app`。
- RATE_LIMIT_MAX 必须在导入 main 之前设置：限流中间件在 import 时读环境变量，
  一套测试会发十几个请求，不放开会触发 429。
"""
import os

os.environ["RATE_LIMIT_MAX"] = "1000"

import pytest
from fastapi.testclient import TestClient

import db as db_module
import main as main_module
from db import FakeDB
from dependencies import get_db
from main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """每个测试独享一个空库和 TestClient，互不污染：

    - DATA_FILE / AUDIT_LOG 重定向到 tmp_path，测试不读写真实的
      data/agents.json 和 audit.log
    - 预写空 JSON 绕过 3 条种子数据，用例从确定的空库开始（id 从 1 计）
    - dependency_overrides 把路由依赖的单例换成测试专用的 FakeDB
    """
    data_file = tmp_path / "agents.json"
    data_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(db_module, "DATA_FILE", data_file)
    monkeypatch.setattr(main_module, "AUDIT_LOG", tmp_path / "audit.log")

    fresh_db = FakeDB()
    app.dependency_overrides[get_db] = lambda: fresh_db
    yield TestClient(app)
    app.dependency_overrides.clear()
