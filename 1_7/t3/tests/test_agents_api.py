"""CRUD API 集成测试 —— 对应题目 3 的六条要求：

1. 创建 Agent → 201 + 字段值正确
2. 查询列表 → 列表结构
3. 查询单个 → 200（存在）/ 404（不存在）
4. 更新 → 只更新传入的字段
5. 删除 → 删除后查询返回 404

client fixture 见根目录 conftest.py：每个测试拿到独立的空库。
"""


def make_payload(**overrides) -> dict:
    """构造创建 Agent 的请求体，overrides 覆盖默认值"""
    payload = {
        "name": "TestAgent",
        "description": "用于测试的 Agent",
        "model": "gpt-4o",
        "temperature": 0.7,
        "tools": [],
        "system_prompt": "",
    }
    payload.update(overrides)
    return payload


# ---------- 创建 ----------

def test_create_agent_returns_201_with_correct_fields(client):
    payload = {
        "name": "CodeReviewer",
        "description": "审查代码并给出建议",
        "model": "deepseek-v3",
        "temperature": 0.3,
        "tools": ["python", "git"],
        "system_prompt": "你是编程助手",
    }
    resp = client.post("/agents/", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    for key, value in payload.items():
        assert body[key] == value, f"字段 {key} 回传值不正确"
    assert body["id"] == 1               # 空库自增从 1 开始
    assert body["status"] == "active"    # 服务端补的默认状态
    assert body["created_at"] == body["updated_at"]


def test_create_agent_with_minimal_body_applies_defaults(client):
    resp = client.post("/agents/", json={"name": "Mini"})

    assert resp.status_code == 201
    body = resp.json()
    assert body["model"] == "gpt-4o"
    assert body["temperature"] == 0.7
    assert body["tools"] == []
    assert body["description"] == ""
    assert body["status"] == "active"


# ---------- 查询列表 ----------

def test_list_agents_returns_list_structure(client):
    client.post("/agents/", json=make_payload(name="A1"))
    client.post("/agents/", json=make_payload(name="A2"))

    resp = client.get("/agents/")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"total", "page", "page_size", "items"}
    assert isinstance(body["items"], list)
    assert body["total"] == 2
    assert [item["name"] for item in body["items"]] == ["A1", "A2"]


# ---------- 查询单个 ----------

def test_get_existing_agent_returns_200(client):
    created = client.post("/agents/", json=make_payload(name="Finder")).json()

    resp = client.get(f"/agents/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Finder"


def test_get_missing_agent_returns_404(client):
    resp = client.get("/agents/999")

    assert resp.status_code == 404
    assert "999" in resp.json()["detail"]


# ---------- 更新 ----------

def test_update_only_changes_provided_fields(client):
    created = client.post(
        "/agents/",
        json=make_payload(name="Updator", temperature=0.9, tools=["python"]),
    ).json()

    resp = client.patch(f"/agents/{created['id']}", json={"temperature": 0.1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["temperature"] == 0.1    # 传入的字段被更新
    assert body["updated_at"] >= created["updated_at"]
    for field in ("name", "description", "model", "tools", "system_prompt", "status"):
        assert body[field] == created[field], f"未传入的字段 {field} 不应被改动"


# ---------- 删除 ----------

def test_delete_then_get_returns_404(client):
    created = client.post("/agents/", json=make_payload(name="Doomed")).json()

    resp = client.delete(f"/agents/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert client.get(f"/agents/{created['id']}").status_code == 404
