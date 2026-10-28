"""模拟数据库（t6 改造版）—— 数据持久化到 JSON 文件

- 服务启动时从 data/agents.json 加载
- create / update / delete 每次修改后立即写回文件（写穿）
- 首次运行（无数据文件）时播种 3 条演示数据，方便直接测试
正式课替换为 SQLAlchemy + PostgreSQL 后，这一层换掉即可，路由层不动
"""
from datetime import datetime
import copy
import json
from pathlib import Path

# 数据文件固定在 t6/data/ 下，与启动时的工作目录无关
DATA_FILE = Path(__file__).resolve().parent / "data" / "agents.json"

# 首次运行的演示数据：名字故意不同，方便测模糊搜索。
# 字段与 CreateAgentRequest 的默认值保持一致（种子数据绕过了 Pydantic 校验，
# 少写字段会导致 AgentResponse 校验失败 500）
SEED_AGENTS = [
    {"name": "CodeReviewer", "description": "审查代码并给出改进建议", "model": "gpt-4o",
     "temperature": 0.7, "tools": [], "system_prompt": ""},
    {"name": "DocWriter", "description": "根据大纲生成技术文档", "model": "deepseek-chat",
     "temperature": 0.7, "tools": [], "system_prompt": ""},
    {"name": "DataAnalyst", "description": "分析表格数据并输出结论", "model": "gpt-4o",
     "temperature": 0.7, "tools": [], "system_prompt": ""},
]


class FakeDB:
    def __init__(self):
        self._data: dict[int, dict] = {}
        self._next_id = 1
        self._load()

    # ---------- 持久化 ----------

    def _load(self) -> None:
        """启动时加载；文件不存在则播种演示数据并立即落盘"""
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw:
                item["created_at"] = datetime.fromisoformat(item["created_at"])
                item["updated_at"] = datetime.fromisoformat(item["updated_at"])
                self._data[item["id"]] = item
            self._next_id = max(self._data, default=0) + 1
        else:
            for seed in SEED_AGENTS:
                self.create(dict(seed))

    def _save(self) -> None:
        """把内存数据整体写回 JSON（数据量小，整写比增量简单可靠）"""
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for item in self._data.values():
            row = copy.deepcopy(item)
            row["created_at"] = row["created_at"].isoformat()
            row["updated_at"] = row["updated_at"].isoformat()
            rows.append(row)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    # ---------- CRUD ----------

    def create(self, item: dict) -> dict:
        now = datetime.now()
        item["id"] = self._next_id
        item["created_at"] = now
        item["updated_at"] = now
        item.setdefault("status", "active")
        self._data[self._next_id] = copy.deepcopy(item)
        self._next_id += 1
        self._save()
        return dict(self._data[item["id"]])

    def get(self, id_: int) -> dict | None:
        item = self._data.get(id_)
        return dict(item) if item else None

    def list_all(self) -> list[dict]:
        return [dict(v) for v in self._data.values()]

    def search(self, keyword: str) -> list[dict]:
        """按名称模糊搜索（大小写不敏感）"""
        kw = keyword.lower()
        return [
            dict(v) for v in self._data.values()
            if kw in v.get("name", "").lower()
        ]

    def update(self, id_: int, updates: dict) -> dict | None:
        item = self._data.get(id_)
        if item is None:
            return None
        for key, value in updates.items():
            if value is not None:
                item[key] = value
        item["updated_at"] = datetime.now()
        self._save()
        return dict(item)

    def delete(self, id_: int) -> bool:
        if id_ in self._data:
            del self._data[id_]
            self._save()
            return True
        return False


# 全局单例
agent_db = FakeDB()
