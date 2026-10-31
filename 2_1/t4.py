import json

task = {
    "id": "task-001",
    "title": "写一个 Agent",
    "completed": False,
    "tools_used": ["search", "read_file", "execute"],
    "duration_seconds": 45.6,
    "result": None
}

dump = json.dumps(task, ensure_ascii=False, indent=2)
print(dump)
load = json.loads(dump)
print(load)
