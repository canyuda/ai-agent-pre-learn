"""并行 vs 串行：对比串行 await 与 asyncio.gather 并发抓取多个 URL 的耗时。

题目要求：编写 fetch_all_urls(urls: list[str])，
- 串行版：for 循环 + await，逐个请求，总耗时约为各请求耗时之和；
- 并行版：asyncio.gather() 同时发起全部请求，总耗时约为最慢一个请求的耗时。

测试 URL 使用 https://httpbin.org/delay/1（服务端固定延迟 1 秒后响应），复制 3 次。
"""

import asyncio
import time

import httpx

# 目标 URL 列表：同一个地址复制 3 次，服务端对每次请求都延迟约 1 秒
URLS = ["https://httpbin.org/delay/1"] * 3

# 单请求超时（秒）：httpbin.org 网络往返较慢，需放宽超时避免误报失败
REQUEST_TIMEOUT = 30


async def fetch(client: httpx.AsyncClient, url: str) -> str:
    """抓取单个 URL，返回响应体文本。

    :param client: 复用的 httpx 异步客户端
    :param url: 目标地址
    :return: 响应体文本
    """
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.text


async def fetch_all_urls(urls: list[str]) -> list[str]:
    """串行版抓取：for 循环 + await，前一个请求完成后才发起下一个。

    :param urls: 目标地址列表
    :return: 按请求顺序排列的响应体列表
    """
    results = []
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for url in urls:
            print(f"  [串行] 请求 {url} ...")
            text = await fetch(client, url)
            results.append(text)
            print(f"  [串行] 完成，响应长度 {len(text)} 字符")
    return results


async def fetch_all_urls_parallel(urls: list[str]) -> list[str]:
    """并行版抓取：asyncio.gather 同时发起全部请求，共享同一个客户端连接池。

    :param urls: 目标地址列表
    :return: 按传入顺序排列的响应体列表（gather 保持参数顺序）
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        print(f"  [并行] 同时发起 {len(urls)} 个请求 ...")
        return await asyncio.gather(*(fetch(client, url) for url in urls))


async def main():
    """主函数：分别执行串行与并行抓取，打印两者耗时及对比结果。"""
    print(f"目标 URL x{len(URLS)}: {URLS[0]}")
    print("=" * 46)

    # 串行执行
    print("=== 串行（for 循环 + await）===")
    start = time.perf_counter()
    serial_results = await fetch_all_urls(URLS)
    serial_time = time.perf_counter() - start
    print(f"=== 串行完成：{len(serial_results)} 个响应，耗时 {serial_time:.2f} 秒 ===\n")

    # 并行执行
    print("=== 并行（asyncio.gather）===")
    start = time.perf_counter()
    parallel_results = await fetch_all_urls_parallel(URLS)
    parallel_time = time.perf_counter() - start
    print(f"=== 并行完成：{len(parallel_results)} 个响应，耗时 {parallel_time:.2f} 秒 ===\n")

    # 对比结果
    print("=" * 46)
    print("执行时间对比")
    print("=" * 46)
    print(f"串行耗时: {serial_time:.2f} 秒 (3 个请求逐个等待)")
    print(f"并行耗时: {parallel_time:.2f} 秒 (3 个请求同时等待)")
    print(f"并行快了约 {serial_time / parallel_time:.1f} 倍，节省 {serial_time - parallel_time:.2f} 秒")
    print("=" * 46)


if __name__ == "__main__":
    asyncio.run(main())
