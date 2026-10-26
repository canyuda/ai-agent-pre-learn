"""并发搜索聚合器：同时搜索 4 个源，成功数达标即返回合并结果，否则报错。

题目要求：实现 search_all(query: str) 函数，
- 模拟 4 个搜索源（文档库 0.8s、代码库 1.2s、网络 1.5s、缓存 0.3s）；
- 同时搜索所有源；
- 只要成功 >= 2 个源就返回合并结果，否则报错；
- 使用 asyncio.gather(return_exceptions=True) 处理部分失败。

知识点：
- asyncio.gather(..., return_exceptions=True) 不会因单个任务抛异常而中断，
  而是把异常对象按发起顺序放进结果列表，与其他成功结果一一对应；
- 用 isinstance(r, Exception) 把结果列表拆成"成功"与"失败"两组，
  再按成功数量决定返回合并结果还是抛出聚合失败异常。
"""

import asyncio
import time

# 搜索源及各自的模拟耗时（秒）
SOURCES = {
    "缓存": 0.3,
    "文档库": 0.8,
    "代码库": 1.2,
    "网络": 1.5,
}

# 聚合成功所需的最少源数量
MIN_SUCCESS = 2


async def search_source(source: str, latency: float, query: str, fail: bool = False) -> str:
    """模拟搜索一个源：等待 latency 秒后返回结果，fail 为 True 时抛出异常。

    :param source: 源名称
    :param latency: 模拟的搜索耗时（秒）
    :param query: 搜索关键词
    :param fail: 是否模拟该源搜索失败
    :return: 该源的搜索结果文本
    """
    print(f"  [{source}] 开始搜索 ...")
    await asyncio.sleep(latency)
    if fail:
        raise ConnectionError(f"{source} 连接失败")
    print(f"  [{source}] 搜索完成，命中 3 条结果")
    return f"{source}：关于<{query}>的 3 条结果"


async def search_all(query: str, fail_sources: set[str] | None = None) -> list[str]:
    """并发搜索全部源，成功源数量达标则返回合并结果，否则报错。

    :param query: 搜索关键词
    :param fail_sources: 强制模拟失败的源名称集合（用于演示部分失败）
    :return: 所有成功源的结果合并列表
    :raises RuntimeError: 成功源数量少于 MIN_SUCCESS 时抛出
    """
    fail_sources = fail_sources or set()

    # 1. 同时搜索所有源：gather 一次性并发发起全部协程
    #    return_exceptions=True：单个源失败不影响其他源，异常按顺序放进结果列表
    results = await asyncio.gather(
        *(search_source(name, latency, query, fail=name in fail_sources)
          for name, latency in SOURCES.items()),
        return_exceptions=True,
    )

    # 2. 区分成功与失败：异常对象用 isinstance 挑出来，其余即成功结果
    merged = [r for r in results if not isinstance(r, Exception)]
    for failure in (r for r in results if isinstance(r, Exception)):
        print(f"  源失败: {failure}")

    # 3. 成功源达到下限才返回合并结果，否则报错
    if len(merged) < MIN_SUCCESS:
        raise RuntimeError(f"仅 {len(merged)} 个源成功（不足 {MIN_SUCCESS} 个），聚合失败")
    print(f"  {len(merged)}/{len(SOURCES)} 个源成功，达到下限 {MIN_SUCCESS} 个，返回合并结果")
    return merged


async def main():
    """主函数：演示全部源正常聚合与多数源失败报错两种场景。"""
    query = "asyncio 教程"
    sources = ", ".join(f"{name}({latency}s)" for name, latency in SOURCES.items())
    print(f"搜索词: {query}")
    print(f"搜索源: {sources}")
    print("=" * 46)

    # 场景一：4 个源全部可用，聚合成功，耗时约等于最慢的网络 1.5 秒
    print("=== 场景一：全部源正常 ===")
    start = time.perf_counter()
    merged = await search_all(query)
    elapsed = time.perf_counter() - start
    print(f"合并结果共 {len(merged)} 条，实际耗时 {elapsed:.2f} 秒 (并发等待最慢的网络 1.5 秒)\n")

    # 场景二：文档库、代码库、网络 3 个源失败，只剩缓存 1 个源成功，低于下限报错
    print("=== 场景二：3 个源失败（仅缓存成功）===")
    start = time.perf_counter()
    try:
        await search_all(query, fail_sources={"文档库", "代码库", "网络"})
    except RuntimeError as e:
        elapsed = time.perf_counter() - start
        print(f"聚合报错: {e} (实际耗时 {elapsed:.2f} 秒)")


if __name__ == "__main__":
    asyncio.run(main())
