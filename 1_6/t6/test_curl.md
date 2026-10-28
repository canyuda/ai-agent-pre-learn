# t6 测试命令手册

完整 CRUD + 文件持久化 + 模糊搜索 + IP 限流 + 操作审计。

## 启动

```bash
cd ai-agent-pre-learn/1_6/t6
../.venv/bin/python -m uvicorn main:app --reload --port 8300
```

首次启动（无 `data/agents.json`）会自动播种 3 条演示数据：
`CodeReviewer`、`DocWriter`、`DataAnalyst`。

> **限流提醒**：同一 IP 每 10 秒最多 5 次请求（超限返回 429）。
> 下面的命令如果连续快速执行，可能中途触发 429——等 10 秒再继续即可。
> 压测时可用环境变量放开：`RATE_LIMIT_MAX=1000 python -m uvicorn main:app ...`

以下命令均在另一个终端执行，`AGENTS` 变量指向服务地址：

```bash
AGENTS=http://127.0.0.1:8300
```

## 1. 健康检查

```bash
curl -s $AGENTS/health
# {"status":"healthy"}
```

## 2. 列表（验证启动加载 / 播种）

```bash
curl -s "$AGENTS/agents/" | python3 -m json.tool
# 首次启动应看到 3 条种子数据，total=3
```

## 3. 创建（带操作人 X-User）

```bash
curl -s -X POST "$AGENTS/agents/" \
  -H 'Content-Type: application/json' \
  -H 'X-User: cyd' \
  -d '{
    "name": "TestBot",
    "description": "用于测试的机器人",
    "model": "deepseek-chat"
  }'
# 返回 201，带 id / created_at / updated_at，记住这个 id（下面假设是 4）
```

## 4. 查询单个

```bash
curl -s "$AGENTS/agents/4" | python3 -m json.tool
```

## 5. 模糊搜索（新增端点）

```bash
curl -s "$AGENTS/agents/search?q=code" | python3 -m json.tool
# 大小写不敏感，匹配到 CodeReviewer，total=1
```

## 6. 更新（带操作人 X-User）

```bash
curl -s -X PATCH "$AGENTS/agents/4" \
  -H 'Content-Type: application/json' \
  -H 'X-User: cyd' \
  -d '{"description": "更新后的描述"}' | python3 -m json.tool
# updated_at 变化
```

## 7. 删除

```bash
curl -s -X DELETE "$AGENTS/agents/4"
# {"ok":true,"message":"Agent 4 已删除"}
```

## 8. 审计日志（新增）

第 3、6 步成功后，操作已追加到 `t6/audit.log`（每行一个 JSON）：

```bash
cat audit.log
# {"time": "2026-10-28T15:04:05", "user": "cyd", "action": "create", "path": "/agents/", "status": 201}
# {"time": "2026-10-28T15:04:10", "user": "cyd", "action": "update", "path": "/agents/4", "status": 200}
```

不带 `X-User` 头的写操作，操作人记为 `anonymous`。

## 9. 持久化验证（重启不丢数据）

```bash
# 创建一条数据后重启服务（Ctrl+C 再重新启动），再查列表：
curl -s "$AGENTS/agents/" | python3 -m json.tool
# 之前创建的数据还在；也可以直接看文件：
cat data/agents.json
```

## 10. 频率限制（新增）

快速连续发 6 次请求，第 6 次应返回 429：

```bash
for i in 1 2 3 4 5 6; do
  echo "--- 第 $i 次 ---"
  curl -s -o /dev/null -w '%{http_code}\n' "$AGENTS/agents/"
done
# 前 5 次 200，第 6 次 429 + "请求过于频繁"
# 等待 10 秒后窗口滑动，自动恢复
```
