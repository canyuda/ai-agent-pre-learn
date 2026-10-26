"""LLMPool：多 API Key 轮询 + 并发限流的 LLM 调用池。

题目要求：实现 LLMPool 类，封装多个 API Key 的并发调用，
- call(prompt)：轮询选择 Key；遇到 429 自动切换下一个 Key；
  所有 Key 都限流时，等待最短的 Retry-After 后重试；
- call_batch(prompts)：用 Semaphore 控制并发数，结果保持顺序。

知识点：
- asyncio.Semaphore 在协程入口 async with 限流，并发满员时新任务排队等待；
- asyncio.gather 按传入顺序返回结果，天然保持批量调用的顺序；
- 429 响应携带 Retry-After 头（秒数形式），限流轮换 = 轮询游标 + 已试 Key 集合，
  全部 Key 限流时取 min(Retry-After) 等待后重开一轮。

说明：演示用 httpx.MockTransport 模拟服务端"每个 Key 首次请求返回 429
（各自 Retry-After），之后正常"，保证行为可复现；真实使用时去掉
transport 参数即为普通 httpx.AsyncClient 请求。
"""

import asyncio
import json
import time

import httpx

# 演示用的 API Key 池
API_KEYS = ["sk-key-1", "sk-key-2", "sk-key-3", "sk-key-4"]

# 模拟服务端限流策略：每个 Key 首次请求返回 429，Retry-After 各不相同（秒）
MOCK_RETRY_AFTER = {
    "sk-key-1": 2,
    "sk-key-2": 1,
    "sk-key-3": 0.5,
    "sk-key-4": 0.8,
}

# 模拟服务端记录每个 Key 已收到的请求次数
_mock_call_counts: dict[str, int] = {}


def _mock_llm_handler(request: httpx.Request) -> httpx.Response:
    """MockTransport 处理器：模拟"首请求限流、之后正常"的 LLM 服务端。"""
    key = request.headers.get("Authorization", "")
    _mock_call_counts[key] = _mock_call_counts.get(key, 0) + 1
    if _mock_call_counts[key] == 1:
        return httpx.Response(
            429,
            headers={"Retry-After": str(MOCK_RETRY_AFTER[key])},
            json={"error": "rate_limited"},
        )
    body = json.loads(request.read())
    return httpx.Response(200, text=f"{body['prompt']} -> 好的（由 {key} 生成）")


def _parse_retry_after(value: str | None) -> float:
    """解析 Retry-After 响应头（秒数形式），缺失或非法时回退 1 秒。"""
    try:
        return max(float(value), 0.0)
    except (TypeError, ValueError):
        return 1.0


class LLMPool:
    """封装多个 API Key 的 LLM 调用池：轮询 Key、429 自动轮换、并发限流。"""

    def __init__(self, api_keys: list[str], max_concurrent: int = 5):
        """初始化：多个 API Key（用于绕过限流），限制最大并发数。

        :param api_keys: API Key 列表
        :param max_concurrent: 最大并发请求数
        """
        self._api_keys = api_keys
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._key_index = 0  # 轮询游标：跨调用持续轮转，均摊各 Key 用量
        self._active = 0     # 当前并发数（用于演示打印）
        self._client: httpx.AsyncClient | None = None

    # ---------- 内部工具 ----------

    def _get_client(self) -> httpx.AsyncClient:
        """惰性创建 AsyncClient；演示用 MockTransport，真实使用去掉 transport 即可。"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                transport=httpx.MockTransport(_mock_llm_handler), timeout=10
            )
        return self._client

    async def _post(self, key: str, prompt: str) -> httpx.Response:
        """用指定 Key 发起一次补全请求，Key 放在 Authorization 头。

        :param key: 本次使用的 API Key
        :param prompt: 提示词
        :return: httpx 响应对象（可能为 429）
        """
        await asyncio.sleep(0.1)  # 模拟网络往返耗时，让并发重叠在演示中可见
        return await self._get_client().post(
            "https://llm.example.com/v1/chat",
            headers={"Authorization": key},
            json={"prompt": prompt},
        )

    # ---------- 对外接口 ----------

    async def call(self, prompt: str) -> str:
        """调用 LLM：轮询选 Key，429 自动切换，全部限流则按最短 Retry-After 重试。

        :param prompt: 提示词
        :return: 模型回复文本
        """
        tried: dict[str, float] = {}  # 本轮已尝试且被限流的 Key -> 其 Retry-After
        while True:
            # 轮询选择 API Key：游标递增取模，跨调用持续轮转
            key = self._api_keys[self._key_index % len(self._api_keys)]
            self._key_index += 1

            resp = await self._post(key, prompt)
            if resp.status_code != 429:
                resp.raise_for_status()
                return resp.text

            retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            tried[key] = retry_after
            print(f"  [429] {key} 被限流 (Retry-After={retry_after}s)，切换下一个 Key")

            # 所有 Key 都试过且全部限流：等待最短 Retry-After 后重开一轮
            if len(tried) >= len(self._api_keys):
                wait = min(tried.values())
                print(f"  [429] 全部 {len(tried)} 个 Key 均限流，"
                      f"等待最短 Retry-After {wait}s 后重试")
                await asyncio.sleep(wait)
                tried.clear()

    async def _call_limited(self, prompt: str) -> str:
        """带并发限制的单次调用：信号量满员时，新任务在此排队等待。

        :param prompt: 提示词
        :return: 模型回复文本
        """
        async with self._semaphore:
            self._active += 1
            print(f"  [并发 {self._active}/{self._max_concurrent}] 提交: {prompt}")
            result = await self.call(prompt)
            self._active -= 1
            return result

    async def call_batch(self, prompts: list[str]) -> list[str]:
        """批量调用：用 Semaphore 控制并发数，结果保持顺序。

        :param prompts: 提示词列表
        :return: 与 prompts 顺序一一对应的结果列表（gather 天然保序）
        """
        return await asyncio.gather(*(self._call_limited(p) for p in prompts))

    async def aclose(self) -> None:
        """关闭底层 HTTP 客户端，释放连接资源。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


async def main():
    """主函数：演示单次调用的 429 轮换重试，以及批量调用的并发限制与保序。"""
    pool = LLMPool(API_KEYS, max_concurrent=2)
    print(f"API Key 数: {len(API_KEYS)}, 最大并发: 2")
    print("=" * 46)

    # 场景一：单次调用——4 个 Key 首次全部限流，等最短的 0.5 秒后重试成功
    print("=== 场景一：单次调用（4 个 Key 首次全部 429）===")
    start = time.perf_counter()
    result = await pool.call("什么是 asyncio？")
    elapsed = time.perf_counter() - start
    print(f"结果: {result}")
    print(f"耗时: {elapsed:.2f} 秒 (4 个 Key 全部 429 后，等最短 Retry-After 0.5 秒重试成功)\n")

    # 场景二：批量调用 6 条，信号量限制并发为 2，结果顺序与输入一致
    print("=== 场景二：批量调用 6 条（并发上限 2）===")
    prompts = [f"问题{i}" for i in range(1, 7)]
    start = time.perf_counter()
    results = await pool.call_batch(prompts)
    elapsed = time.perf_counter() - start
    print("-" * 46)
    for prompt, answer in zip(prompts, results):
        print(f"  {prompt} -> {answer}")
    print(f"共 {len(results)} 条结果，顺序与输入一致，耗时 {elapsed:.2f} 秒")

    await pool.aclose()


if __name__ == "__main__":
    asyncio.run(main())
